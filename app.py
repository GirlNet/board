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
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pinboard_id = db.Column(db.String(100))
    local_position = db.Column(db.String(100)) 
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 数据库初始化 ---
with app.app_context():
    db.create_all() 

# --- 路由：读取留言（关键修复点） ---
@app.route('/notes', methods=['GET'])
def get_notes():
    pid = request.args.get('pinboardId')
    # 如果传了 ID 就过滤，没传就全查
    notes = Note.query.filter_by(pinboard_id=pid).all() if pid else Note.query.all()
    
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
    
    # 核心修复：原作者脚本通常需要数据被包裹在 "notes" 键里 
    return jsonify({"notes": data_dict})

# --- 路由：上传留言 ---
@app.route('/upload', methods=['GET'])
def upload_note():
    try:
        new_note = Note(
            pinboard_id = request.args.get('pinboardId'),
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

# --- 路由：创建/管理 ---
@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

@app.route('/admin')
def admin():
    notes = Note.query.order_by(Note.id.desc()).all()
    return render_template('admin.html', notes=notes)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
