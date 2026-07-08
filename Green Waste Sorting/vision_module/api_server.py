"""
HTTP API 接口 - 机械臂端调用
启动后，机械臂发送 POST 请求获取检测结果
"""

from flask import Flask, request, jsonify
from detector import detect
from pathlib import Path
import tempfile

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect_image():
    """
    接收图片，返回检测结果
    
    机械臂端调用方式：
    import requests
    files = {'image': open('photo.jpg', 'rb')}
    response = requests.post('http://localhost:5000/detect', files=files)
    result = response.json()
    """
    if 'image' not in request.files:
        return jsonify({"error": "没有图片"}), 400
    
    file = request.files['image']
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        file.save(tmp.name)
        result = detect(tmp.name)
    
    if result:
        return jsonify({
            "success": True,
            "data": result
        })
    else:
        return jsonify({
            "success": False,
            "message": "未检测到物体"
        })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "model": "garbage_cls-5"})


if __name__ == '__main__':
    print("="*50)
    print("垃圾检测 API 服务")
    print("地址: http://localhost:5000")
    print("接口:")
    print("  POST /detect  - 上传图片检测")
    print("  GET  /health  - 健康检查")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)