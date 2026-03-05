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
    pinboard_id = db.Column(db.String(100)) # 报错就是因为这一列在数据库里找不到
    local_position = db.Column(db.String(100)) 
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 核心修复逻辑：强制重置表结构 ---
with app.app_context():
    # 注意：运行这一次后，如果 /admin 正常了，建议删掉下面 db.drop_all() 这一行
    # 它会清空你目前数据库里所有的测试数据，但这是修复“列不存在”报错最快的方法
    try:
        # 尝试查询新列，如果报错则触发重置
        db.session.execute(db.text("SELECT pinboard_id FROM note LIMIT 1"))
    except Exception:
        db.session.rollback()
        print("检测到数据库结构过旧，正在重置表...")
        db.drop_all() 
        db.create_all()
        print("数据库已重建，新列 pinboard_id 已就绪。")

# --- 接口逻辑 ---

@app.route('/notes', methods=['GET'])
def get_notes():
    pid = request.args.get('pinboardId')
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
    return jsonify(data_dict)

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

@app.route('/create', methods=['GET'])
def create_board():
    return "OK", 200

@app.route('/admin')
def admin():
    # 只要数据库结构对齐了，这里就不会再报 500 错误
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
