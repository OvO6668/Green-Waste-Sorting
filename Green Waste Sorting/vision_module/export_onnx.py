from ultralytics import YOLO

print("正在加载模型...")
model = YOLO('best.pt')

print("正在导出 ONNX...")
model.export(format='onnx', imgsz=640)

print("✅ ONNX 导出完成！")