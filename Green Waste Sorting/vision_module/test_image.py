"""
测试单张图片
"""

from detector import detect, detect_and_save
import sys

# 测试图片路径（改成你的）
TEST_IMAGE = r"D:\garbageproject\all\all (1).jpg"

if __name__ == '__main__':
    print(f"正在检测: {TEST_IMAGE}")
    
    # 检测并保存结果图
    result = detect_and_save(TEST_IMAGE)
    
    if result:
        print(f"\n✅ 检测到: {result['category_cn']} ({result['category']})")
        print(f"   置信度: {result['confidence']}")
        print(f"   中心坐标: ({result['center']['x']}, {result['center']['y']})")
        print(f"   结果图保存在: results/result_all (1).jpg")
    else:
        print("❌ 未检测到物体")