from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import json
import os

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="171272812288197",
    api_secret="HEX6ayHSRPpjai6vC8oghdDFUEY"
)

USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
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
    return send_from_directory(os.path.join(app.root_path, 'static'), path)

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

    users[username] = {"password": generate_password_hash(password), "points": 1}
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

    if username not in users or not check_password_hash(users[username]['password'], password):
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

    if 'file' not in request.files and 'text_essay' not in request.form:
        return jsonify({'error': 'No file or text provided'}), 400

    file = request.files.get('file')
    text_essay = request.form.get('text_essay')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        upload_result = cloudinary.uploader.upload(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    elif text_essay:
        text_filename = secure_filename(f"{username}_essay.txt")
        text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], text_filename)
        with open(text_filepath, 'w') as text_file:
            text_file.write(text_essay)
        upload_result = cloudinary.uploader.upload(text_filepath)
    else:
        return jsonify({'error': 'No valid file or text provided'}), 400

    users[username]['points'] -= 1
    save_users(users)

    response = jsonify({'message': 'File uploaded successfully', 'cloudinary_url': upload_result['url']})
    response.set_cookie('points', str(users[username]['points']), httponly=True)

    return response, 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)
