import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 优先级：环境变量中的数据库地址 > 本地 SQLite 文件（用于本地测试）
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local_test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 数据库模型定义 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_position = db.Column(db.String(50))
    angle = db.Column(db.String(20))
    color_hue = db.Column(db.String(20))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# 初始化数据库表
with app.app_context():
    db.create_all()

# --- VRChat 接口 ---

# 1. 下载留言 (对应 NoteDownloader.cs)
@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    # 构造 VRChat Udon 能够解析的 JSON 格式
    data_dict = {}
    for n in notes:
        data_dict[str(n.id)] = {
            "localPosition": n.local_position,
            "angle": n.angle,
            "colorHue": n.color_hue,
            "content": n.content,
            "userHash": n.user_hash,
            "timestamp": n.timestamp
        }
    return jsonify(data_dict)

# 2. 上传留言 (对应 NoteUploader.cs)
@app.route('/upload', methods=['GET'])
def upload_note():
    try:
        new_note = Note(
            local_position = request.args.get('localPosition'),
            angle = request.args.get('angle'),
            color_hue = request.args.get('colorHue'),
            content = request.args.get('content'),
            user_hash = request.args.get('userHash'),
            timestamp = float(datetime.now().timestamp() * 1000) # 转为毫秒
        )
        db.session.add(new_note)
        db.session.commit()
        return "Upload Success", 200
    except Exception as e:
        return str(e), 400

# 3. 初始化接口 (对应 418 错误处理)
@app.route('/create', methods=['GET'])
def create_board():
    return "Pinboard Initialized", 201

# --- 管理后台 ---

@app.route('/admin')
def admin_page():
    notes = Note.query.order_by(Note.id.desc()).all()
    return render_template('admin.html', notes=notes)

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return "Deleted", 200

if __name__ == '__main__':
    # 端口号设为 5000，Render 会自动识别
    app.run(host='0.0.0.0', port=5000)
