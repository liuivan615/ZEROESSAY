from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_users():
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def index():
    return send_from_directory(app.root_path, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(app.root_path, path)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.root_path + '/static', path)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    users = load_users()
    if username in users:
        return jsonify({'error': 'User already exists'}), 400

    if len(password) < 5:
        return jsonify({'error': 'Password must be at least 5 characters long'}), 400

    users[username] = {"password": password, "points": 1}
    save_users(users)

    response = jsonify({'message': 'Registration successful'})
    response.set_cookie('username', username, httponly=True)
    response.set_cookie('points', '1', httponly=True)

    return response, 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    users = load_users()

    if username not in users or users[username]['password'] != password:
        return jsonify({'error': 'Invalid username or password'}), 400

    response = jsonify({'message': 'Login successful'})
    response.set_cookie('username', username, httponly=True)
    response.set_cookie('points', str(users[username]['points']), httponly=True)

    return response, 200

@app.route('/upload', methods=['POST'])
def upload():
    username = request.cookies.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 400

    users = load_users()
    if users[username]['points'] < 1:
        return jsonify({'error': 'Insufficient points'}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    users[username]['points'] -= 1
    save_users(users)

    response = jsonify({'message': 'File uploaded successfully'})
    response.set_cookie('points', str(users[username]['points']), httponly=True)

    return response, 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
