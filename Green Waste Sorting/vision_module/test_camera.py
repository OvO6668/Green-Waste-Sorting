"""
摄像头实时检测 - 按 Q 退出
"""

import cv2
from detector import detect

# 摄像头编号（0=默认摄像头，1=外接摄像头）
CAMERA_ID = 0

def main():
    cap = cv2.VideoCapture(CAMERA_ID)
    
    if not cap.isOpened():
        print("❌ 摄像头打不开！")
        return
    
    print("摄像头已启动，按 Q 退出...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 保存当前帧（临时文件）
        temp_path = "temp_frame.jpg"
        cv2.imwrite(temp_path, frame)
        
        # 检测
        result = detect(temp_path, conf=0.25)
        
        # 在画面上画结果
        if result:
            # 画框
            bbox = result['bbox']
            x1, y1, x2, y2 = int(bbox['x1']), int(bbox['y1']), int(bbox['x2']), int(bbox['y2'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 写文字
            label = f"{result['category_cn']} {result['confidence']}"
            cv2.putText(frame, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示坐标
            cx, cy = int(result['center']['x']), int(result['center']['y'])
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"({cx}, {cy})", (cx+10, cy), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        cv2.imshow('Garbage Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("摄像头已关闭")


if __name__ == '__main__':
    main()