"""
垃圾检测模块 - 视觉负责人使用
输出：类别、置信度、坐标（给机械臂）
"""

from ultralytics import YOLO
from pathlib import Path
import json

# ========== 配置 ==========
MODEL_PATH = Path(__file__).parent / "best.pt"  # 模型路径（自动在当前文件夹找）

# 类别对应表（和你训练时一致）
CLASS_NAMES = ['hazardous', 'kitchen', 'recyclables', 'residual']
CLASS_NAMES_CN = {
    'hazardous': '有害垃圾',
    'kitchen': '厨余垃圾', 
    'recyclables': '可回收垃圾',
    'residual': '其他垃圾'
}

# 加载模型（只加载一次，避免重复）
print("正在加载模型...")
model = YOLO(str(MODEL_PATH))
print("模型加载完成！")


def detect(image_path, conf=0.25):
    """
    检测单张图片中的垃圾
    
    参数:
        image_path: 图片路径
        conf: 置信度阈值（默认0.25）
    
    返回:
        dict: 检测结果，包含 category, confidence, bbox, center
        None: 没有检测到物体
    """
    results = model(image_path, conf=conf, verbose=False)
    
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)
            conf_val = float(box.conf)
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            
            detection = {
                "category": CLASS_NAMES[cls_id],           # 英文类别
                "category_cn": CLASS_NAMES_CN[CLASS_NAMES[cls_id]],  # 中文类别
                "category_id": cls_id,                       # 类别编号
                "confidence": round(conf_val, 3),           # 置信度
                "bbox": {                                   # 边框坐标
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "x2": round(x2, 1),
                    "y2": round(y2, 1)
                },
                "center": {                                 # 中心点（机械臂用）
                    "x": round((x1 + x2) / 2, 1),
                    "y": round((y1 + y2) / 2, 1)
                }
            }
            detections.append(detection)
    
    # 返回置信度最高的结果
    if detections:
        best = max(detections, key=lambda x: x["confidence"])
        return best
    
    return None


def detect_and_save(image_path, save_dir=None):
    """
    检测并保存结果图（带标注框）
    
    参数:
        image_path: 图片路径
        save_dir: 保存目录（默认当前文件夹下的 results）
    """
    if save_dir is None:
        save_dir = Path(__file__).parent / "results"
    
    save_dir = Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    
    # 检测
    results = model(image_path, conf=0.25, verbose=False)
    
    # 保存标注图
    for r in results:
        r.save(filename=str(save_dir / f"result_{Path(image_path).name}"))
    
    # 返回检测结果
    return detect(image_path)


if __name__ == '__main__':
    # 测试
    test_img = r"D:\garbageproject\all\all (1).jpg"
    result = detect(test_img)
    
    if result:
        print("\n" + "="*50)
        print("检测结果：")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("="*50)
    else:
        print("未检测到物体")