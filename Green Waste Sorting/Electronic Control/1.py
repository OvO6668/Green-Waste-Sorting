#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
绿途智分 - RDK X5 上位机视觉识别系统
============================================================
硬件: RDK X5 开发板 (旭日X3芯片, 10TOPS算力)
摄像头: 800万AF自动对焦 USB2.0 IMX179
模型: YOLO11 轻量化目标检测
功能: 识别垃圾类别，通过串口发送坐标给Arduino机械臂
通信: UART串口 (/dev/ttyS3 或 /dev/ttyUSB0)
============================================================
"""

import cv2
import numpy as np
import serial
import serial.tools.list_ports
import threading
import time
import json
import argparse
import sys
from collections import deque, Counter
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict

# ===================== 尝试导入YOLO推理库 =====================
try:
    from hobot_dnn import pyeasy_dnn as dnn
    RDK_MODE = True
    print("[INFO] RDK X5 DNN模块加载成功，启用BPU加速")
except ImportError:
    RDK_MODE = False
    print("[WARN] 未检测到RDK DNN模块，使用OpenCV DNN模式（PC调试）")

# ===================== 配置参数 =====================
@dataclass
class Config:
    # 摄像头参数
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 1280
    CAMERA_HEIGHT: int = 720
    AUTOFOCUS: bool = True
    
    # 串口参数
    SERIAL_PORT: str = "/dev/ttyS3"
    SERIAL_BAUD: int = 115200
    SERIAL_TIMEOUT: float = 1.0
    
    # 模型参数
    MODEL_PATH: str = "/opt/models/yolo11_garbage.bin"
    MODEL_INPUT_SIZE: Tuple[int, int] = (640, 640)
    CONFIDENCE_THRESHOLD: float = 0.65
    NMS_THRESHOLD: float = 0.45
    
    # 垃圾类别定义（与Arduino端严格一致）
    CLASS_NAMES: List[str] = field(default_factory=lambda: [
        "recyclable",    # 0: 可回收物
        "kitchen",       # 1: 厨余垃圾
        "hazardous",     # 2: 有害垃圾
        "other"          # 3: 其他垃圾
    ])
    CLASS_COLORS: List[Tuple[int, int, int]] = field(default_factory=lambda: [
        (0, 255, 0),     # 绿 - 可回收
        (0, 165, 255),   # 橙 - 厨余
        (0, 0, 255),     # 红 - 有害
        (128, 128, 128)  # 灰 - 其他
    ])
    
    # 坐标转换（像素 -> 机械臂实际坐标 mm）
    PIXEL_TO_MM_X: float = 0.5
    PIXEL_TO_MM_Y: float = 0.5
    PLATFORM_CENTER_X: int = 640
    PLATFORM_CENTER_Y: int = 360
    
    # 系统参数
    DETECTION_INTERVAL: float = 0.1
    STABLE_FRAMES: int = 3
    TIMEOUT_SECONDS: float = 3.0
    MAX_FPS: int = 30

config = Config()

# ===================== 通信协议 =====================
class Protocol:
    FRAME_HEADER = bytes([0xAA, 0x55])
    FRAME_TAIL = bytes([0x0D, 0x0A])
    
    CMD_HEARTBEAT = 0x01
    CMD_IDENTIFY = 0x10       # 发送识别结果：类别 + 坐标X + 坐标Y
    CMD_GRAB_START = 0x20     # Arduino请求开始抓取
    CMD_STATUS_REQ = 0x30
    CMD_STATUS_RSP = 0x31
    CMD_ERROR = 0x40
    CMD_ACK = 0x50

# ===================== 串口通信类 =====================
class SerialCommunicator:
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        self.ser: Optional[serial.Serial] = None
        self.connected = False
        self.rx_buffer = bytearray()
        self.lock = threading.Lock()
        self.arduino_state = "IDLE"
        self.task_active = False
        self._stop_event = threading.Event()
        
    def connect(self) -> bool:
        """连接Arduino，支持自动重试"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=config.SERIAL_TIMEOUT,
                write_timeout=1.0
            )
            self.connected = True
            self._stop_event.clear()
            print(f"[SERIAL] 已连接: {self.port} @ {self.baud}bps")
            
            self.rx_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.rx_thread.start()
            return True
        except Exception as e:
            print(f"[ERROR] 串口连接失败: {e}")
            print(f"[HINT] 可用串口: {[p.device for p in serial.tools.list_ports.comports()]}")
            return False
    
    def disconnect(self):
        self._stop_event.set()
        self.connected = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SERIAL] 已断开")
    
    def _receive_loop(self):
        while not self._stop_event.is_set():
            try:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    with self.lock:
                        self.rx_buffer.extend(data)
                        self._parse_buffer()
            except serial.SerialException:
                break
            except Exception as e:
                print(f"[ERROR] 串口接收异常: {e}")
            time.sleep(0.005)
    
    def _parse_buffer(self):
        while True:
            header_idx = self.rx_buffer.find(Protocol.FRAME_HEADER)
            if header_idx == -1:
                break
            tail_idx = self.rx_buffer.find(Protocol.FRAME_TAIL, header_idx + 2)
            if tail_idx == -1:
                break
            
            frame = self.rx_buffer[header_idx:tail_idx + 2]
            self.rx_buffer = self.rx_buffer[tail_idx + 2:]
            self._process_frame(frame)
    
    def _process_frame(self, frame: bytes):
        if len(frame) < 7:
            return
        cmd = frame[2]
        data_len = frame[3]
        
        # 校验和：帧头后到校验和字节前
        payload = frame[2:-3]
        checksum = sum(payload) & 0xFF
        if checksum != frame[-3]:
            print("[WARN] 校验和错误，丢弃帧")
            return
        
        try:
            if cmd == Protocol.CMD_HEARTBEAT:
                states = ["IDLE", "WAITING", "MOVING_GRAB", "GRABBING",
                         "MOVING_DROP", "DROPPING", "RETURNING", "ERROR"]
                if data_len >= 2 and frame[4] < len(states):
                    self.arduino_state = states[frame[4]]
                self.task_active = bool(frame[5]) if data_len >= 3 else False
                
            elif cmd == Protocol.CMD_STATUS_RSP:
                print(f"[ARDUINO] 状态: {self.arduino_state}, "
                      f"任务: {'运行中' if self.task_active else '空闲'}")
                
            elif cmd == Protocol.CMD_ACK:
                print(f"[ARDUINO] 确认: CMD=0x{frame[4]:02X}, PARAM={frame[5]}")
                
            elif cmd == Protocol.CMD_ERROR:
                err_code = frame[4]
                print(f"[ERROR] Arduino报告错误码: 0x{err_code:02X}")
                
        except IndexError:
            print("[WARN] 帧数据长度不足")
    
    def send_frame(self, cmd: int, data: bytes = b"") -> bool:
        if not self.connected or not self.ser:
            return False
        
        frame = bytearray()
        frame.extend(Protocol.FRAME_HEADER)
        frame.append(cmd)
        frame.append(len(data))
        frame.extend(data)
        checksum = sum(frame[2:]) & 0xFF
        frame.append(checksum)
        frame.extend(Protocol.FRAME_TAIL)
        
        try:
            with self.lock:
                self.ser.write(bytes(frame))
    