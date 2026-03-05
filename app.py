import os
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- 1. 数据库配置 ---
uri = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_position = db.Column(db.String(100)) # 修复 UndefinedColumn 报错
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 3. 数据库初始化 (自动修复逻辑) ---
with app.app_context():
    try:
        # 尝试查询。如果字段不存在会报错，此时自动重置表
        db.session.execute(db.select(Note).limit(1))
    except Exception:
        db.session.rollback()
        db.drop_all() 
        db.create_all()
        print("Database tables reset to fix column issues.")
    db.create_all()

# --- 4. 路由定义 ---

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

# --- 5. Admin 管理后台 (已修复引号闭合问题) ---
@app.route('/admin')
def admin():
    notes = Note.query.order_by(Note.id.desc()).all()
    
    # 核心修复点：确保三引号 """ 正确闭合
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>留言板管理后台</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background: #f4f4f9; color: #333; }
            .container { max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #eee; padding: 12px; text-align: left; }
            th { background-color: #5865f2; color: white; }
            tr:hover { background-color: #f1f1f1; }
            .delete-link { color: #ff4b4b; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>VRChat 留言板管理</h1>
            <p>当前记录: {{ notes|length }} 条</p>
            <table>
                <tr>
                    <th>ID</th>
                    <th>内容</th>
                    <th>用户哈希</th>
                    <th>操作</th>
                </tr>
                {% for note in notes %}
                <tr>
                    <td>{{ note.id }}</td>
                    <td>{{ note.content }}</td>
                    <td>{{ note.user_hash }}</td>
                    <td><a href="/delete/{{ note.id }}" class="delete-link" onclick="return confirm('确定删除？')">删除</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, notes=notes)

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return "<script>alert('Deleted'); window.location.href='/admin';</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
