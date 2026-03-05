import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Render 会自动提供 DATABASE_URL 环境变量
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义留言数据库模型
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    user_hash = db.Column(db.String(100))
    # 其他字段如 localPosition, angle 等也在这里定义...

# 在第一次运行前创建表
with app.app_context():
    db.create_all()

@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.all()
    # 转换为 VRChat 需要的格式输出...
    return jsonify({n.id: {"content": n.content} for n in notes})

# 其他接口(upload/admin)同理修改为数据库操作