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
# 增加连接池设置，防止数据库断连
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 增加 pinboard_id 列，虽然你说“无所谓”，但存下来能防止以后数据乱套
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

# --- 路由：读取留言 ---
@app.route('/notes', methods=['GET'])
def get_notes():
    # 尝试按 ID 过滤，如果没传 ID 就全返回，这样最稳
    pid = request.args.get('pinboardId')
    if pid:
        notes = Note.query.filter_by(pinboard_id=pid).all()
    else:
        notes = Note.query.all()

    data_dict = {}
    for n in notes:
        # 这里返回的 Key 必须是小驼峰，Unity 脚本才能识别
        data_dict[str(n.id)] = {
            "localPosition": n.local_position,
            "angle": n.angle,
            "colorHue": n.color_hue,
            "content": n.content,
            "userHash": n.user_hash,
            "timestamp": n.timestamp
        }
    return jsonify(data_dict)

# --- 路由：上传留言 ---
@app.route('/upload', methods=['GET'])
def upload_note():
    try:
        # 这里直接读取原作者链接里的参数名
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
        print(f"Error: {e}")
        return str(e), 500

# --- 路由：创建空间 ---
@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

# --- 路由：管理后台 ---
@app.route('/admin')
def admin():
    notes = Note.query.order_by(Note.id.desc()).all()
    return render_template('admin.html', notes=notes)

# --- 路由：删除留言 ---
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return "OK", 200

if __name__ == '__main__':
    # 动态获取端口，适配 Render 环境
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
