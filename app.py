import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 修正 Render 提供的 postgres:// 为 postgresql://
uri = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 数据库模型 ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_position = db.Column(db.String(100)) # 对应报错中缺失的列
    angle = db.Column(db.String(50))
    color_hue = db.Column(db.String(50))
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    timestamp = db.Column(db.Float)

# --- 数据库自动初始化逻辑 ---
with app.app_context():
    # 如果你之前运行报错，这里可以临时改为 db.drop_all() 然后再 db.create_all()
    # 正常情况下使用 create_all 即可
    db.create_all() 

# --- 接口逻辑 ---

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
        # 获取 Unity 传来的参数
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
    app.run(host='0.0.0.0', port=5000)
