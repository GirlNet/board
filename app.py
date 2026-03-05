import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- 数据库配置：修正 Render 提供的 postgres:// 协议头 ---
uri = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 增加连接池优化，防止 Render 免费版频繁出现数据库断连导致的 502
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
db = SQLAlchemy(app)

# --- 数据库模型：增加了缺失的 pinboard_id 字段 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pinboard_id = db.Column(db.String(100)) # 核心修复：存储房间ID
    local_position = db.Column(db.String(100)) 
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 数据库自动初始化逻辑 ---
with app.app_context():
    # 强制创建表结构。如果你依然遇到列缺失报错，
    # 请手动在 Render 部署时运行一次 db.drop_all() 再 db.create_all()
    db.create_all() 

# --- 接口逻辑 ---

@app.route('/notes', methods=['GET'])
def get_notes():
    # 获取 Unity 传来的 ID
    pid = request.args.get('pinboardId')
    # 只查询对应 ID 的留言，防止数据混淆
    if pid:
        notes = Note.query.filter_by(pinboard_id=pid).all()
    else:
        notes = Note.query.all()

    data_dict = {}
    for n in notes:
        # 这里转换成原作者脚本认得的小驼峰命名，解决“数据隐藏”问题
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
        # 直接读取原作者脚本生成的参数名
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
        print(f"Upload error: {e}")
        return str(e), 500

@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

@app.route('/admin')
def admin():
    # 按 ID 倒序排列，解决你看到的查询报错
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
    # 核心修复：适配 Render 随机分配的端口，防止部署失败
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
