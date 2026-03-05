@app.route('/notes', methods=['GET'])
def get_notes():
    # 逻辑代码...
    return jsonify(data_dict)

@app.route('/upload', methods=['GET'])
def upload_note():
    # 逻辑代码...
    return "OK", 200

@app.route('/create', methods=['GET'])
def create_board():
    return "Created", 201
