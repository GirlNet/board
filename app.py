from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = 'notes.json'

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

# 1. 对应 NoteDownloader.cs 的下载请求
@app.route('/notes', methods=['GET'])
def get_notes():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return jsonify(data)

# 2. 对应 NoteUploader.cs 的上传请求
@app.route('/upload', methods=['GET'])
def upload_note():
    # 从 URL 参数获取数据
    note_data = {
        "localPosition": request.args.get('localPosition'),
        "angle": request.args.get('angle'),
        "colorHue": request.args.get('colorHue'),
        "content": request.args.get('content'),
        "userHash": request.args.get('userHash'),
        "timestamp": request.args.get('timestamp', 0)
    }
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    # 使用时间戳作为 Key
    note_id = str(len(data) + 1)
    data[note_id] = note_data
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
        
    return "Success", 200

# 3. 对应 CreatePinboard 请求
@app.route('/create', methods=['GET'])
def create():
    return "Created", 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
