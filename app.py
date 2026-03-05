import os
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- 1. 数据库配置与环境适配 ---
# 自动处理 Render 的 postgres:// 到 postgresql:// 的转换
uri = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. 数据库模型定义 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_position = db.Column(db.String(100)) # 修复之前报错缺失的列
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 3. 数据库初始化 ---
with app.app_context():
    # 第一次运行或字段报错时，取消下面这一行的注释来强制重置表结构
    # db.drop_all() 
    db.create_all()

# --- 4. 路由定义 (解决 404 问题) ---

@app.route('/')
def index():
    return "VRChat Pinboard Server is Running!", 200

# 对应 NoteDownloader.cs
@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
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

# 对应 NoteUploader.cs
@app.route('/upload', methods=['GET'])
def upload_note():
    try:
        new_note = Note(
            local_position = request.args.get('localPosition'),
            angle = request.args.get('angle'),
            color_hue = request.args.get('colorHue'),
            content = request.args.get('content'),
            user_hash = request.args.get('userHash'),
            timestamp = float(datetime.now().timestamp() * 1000)
        )
        db.session.add(new_note)
        db.session.commit()
        return "OK", 200
    except Exception as e:
        return str(e), 500

@app.route('/create', methods=['GET'])
def create_board():
    return "Created", 201

# 管理后台 (使用 render_template_string 避免缺少 html 文件导致 404)
@app.route('/admin')
def admin():
    notes = Note.query.order_by(Note.id.desc()).all()
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>留言板管理</title>
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            tr:nth-child(even) { background-color: #f2 f2 f2; }
        </style>
    </head>
    <body>
        <h1>所有留言记录</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>内容</th>
                <th>位置</th>
                <th>用户Hash</th>
                <th>时间</th>
            </tr>
            {% for note in notes %}
            <tr>
                <td>{{ note.id }}</td>
                <td>{{ note.content }}</td>
                <td>{{ note.local_
