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
# 增加重连机制，减少 502 报错
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pinboard_id = db.Column(db.String(100)) # 这一列就是导致你刚才报错的“失踪人口”
    local_position = db.Column(db.String(100))
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 数据库强制初始化逻辑 ---
with app.app_context():
    # 只要检测到数据库还没更新，就强制重置表结构
    # 第一次部署后，如果你看到 /admin 能打开了，可以删掉下面这两行
    try:
        db.create_all()
        # 尝试查询新字段，如果报错说明需要重置
        Note.query.with_entities(Note.pinboard_id).first()
    except Exception:
        db.session.rollback()
        db.drop_all()
        db.create_all()
        print("数据库结构已重置，pinboard_id 列已添加。")

# --- 接口逻辑 ---

@app.route('/notes', methods=['GET'])
def get_notes():
    pid = request.args.get('pinboardId')
    # 兼容性查询：如果带了 ID 就过滤，没带就全查
    if pid:
        notes = Note.query.filter_by(pinboard_id=pid).all()
    else:
        notes = Note.query.all()

    data_dict = {}
    for n in notes:
        # 这里转换成原作者脚本认得的小驼峰命名
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
        # 直接读取原作者生成的链接参数
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
        print(f"Upload Error: {e}")
        return str(e), 500

@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

@app.route('/admin')
def admin():
    # 按 ID 倒序排列，最新的留言在最上面
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
    # 适配 Render 的端口环境变量
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
