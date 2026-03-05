import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- 数据库配置 ---
uri = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 增加连接池优化，防止 Render 免费版频繁出现 502
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 核心修复：必须增加这一列，否则无法区分不同地图的留言
    pinboard_id = db.Column(db.String(100)) 
    local_position = db.Column(db.String(100))
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 数据库初始化 ---
with app.app_context():
    # 注意：如果你改了模型（加了列），建议先手动在 Render 数据库删掉旧表
    # 或者临时取消下面这一行的注释运行一次，再改回来：
    # db.drop_all() 
    db.create_all() 

# --- 接口逻辑 ---

@app.route('/notes', methods=['GET'])
def get_notes():
    # 核心修复：只返回当前地图 ID 的留言，防止数据被“隐藏”或混淆
    target_id = request.args.get('pinboardId')
    if target_id:
        notes = Note.query.filter_by(pinboard_id=target_id).all()
    else:
        notes = Note.query.all() # 如果没传 ID，返回所有（兼容调试）

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
        # 接收并存储 pinboardId
        pid = request.args.get('pinboardId')
        content = request.args.get('content')
        
        if not pid or content is None:
            return "Missing ID or Content", 400

        new_note = Note(
            pinboard_id = pid,
            local_position = request.args.get('localPosition'),
            angle = request.args.get('angle'),
            color_hue = request.args.get('colorHue'),
            content = content,
            user_hash = request.args.get('userHash'),
            timestamp = float(datetime.now().timestamp() * 1000)
        )
        db.session.add(new_note)
        db.session.commit()
        return "OK", 200
    except Exception as e:
        print(f"Upload Error: {e}")
        return str(e), 500

@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

@app.route('/admin')
def admin():
    notes = Note.query.order_by(Note.id.desc()).all()
    return render_template('admin.html', notes=notes)

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return "OK", 200

if __name__ == '__main__':
    # Render 部署必须读取 PORT 环境变量
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
