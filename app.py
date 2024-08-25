import os
import time
import base64
import collections
import hashlib
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI, OpenAIError
import json

# Flask应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})

# 配置上传目录
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'ZEROESSAY', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-BFxu0ZFG4LS3M0xd414aAeB1C6234678BbBcAb8000C59696")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.xiaoai.plus/v1")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 图片处理与API调用相关函数
def preprocess_image(image_path):
    image = Image.open(image_path).convert('L')
    enhancer = ImageEnhance.Contrast(image).enhance(2)
    image = enhancer.point(lambda x: 0 if x < 140 else 255, '1')
    image = image.filter(ImageFilter.MedianFilter(size=3))
    return image

def extract_text_with_ocr(image_path):
    try:
        preprocessed_image = preprocess_image(image_path)
        return pytesseract.image_to_string(preprocessed_image).strip()
    except Exception as e:
        return f"Error performing OCR on the image: {str(e)}"

def process_text_with_gpt(prompt):
    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=4096)
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"Error during GPT processing: {str(e)}"

def generate_gpt_prompt(ocr_text, base64_text, user_input_text):
    return f"""
    第一步：识别并提取用户作文中的题目和正文，题目需要中英文表达。

    第二步：根据雅思的四个评分维度对作文进行评分，每个维度的总分为9分，评分请使用中文：
    1. 任务回应（Task Achievement/Task Response）
    2. 连贯与衔接（Coherence and Cohesion）
    3. 词汇资源（Lexical Resource）
    4. 语法多样性与准确性（Grammatical Range and Accuracy）
    最后，计算四个维度的平均分并给出总分（四舍五入到0.5）。

    第三步：逐句分析作文内容，判断是否需要修改。若需修改，请给出修改后的句子（用英文表 达），并解释修改的原因（中文说明）。

    第四步：根据逐句修改生成最终的完整作文。

    OCR识别结果: {ocr_text}
    Base64识别结果: {base64_text}
    用户输入文本: {user_input_text}
    """

# 上传文件处理的API端点
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        text_essay = request.form.get('text_essay')

        if not file and not text_essay:
            return jsonify({'error': 'No file or text part in the request'}), 400

        filepath = None
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        # 提取OCR和Base64内容
        ocr_text = extract_text_with_ocr(filepath) if filepath else ""
        base64_text = get_image_base64(filepath) if filepath else ""

        # 生成GPT提示词
        prompt = generate_gpt_prompt(ocr_text, base64_text, text_essay)

        # 调用GPT获取结果
        result = process_text_with_gpt(prompt)

        # 获取用户信息并扣除积分
        username = request.cookies.get('username')
        users = load_users()

        if username in users and users[username]['points'] > 0:
            users[username]['points'] -= 1  # 扣除积分
            save_users(users)  # 更新用户数据
            response = jsonify({'result': result, 'points': users[username]['points']})
            response.set_cookie('points', str(users[username]['points']), httponly=False)
            return response, 200
        else:
            return jsonify({'error': 'Not enough points or user not logged in'}), 403

    return render_template('upload.html')

# 验证上传的文件格式是否符合要求
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        return None

# 用户注册和登录
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

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

    users[username] = {"password": generate_password_hash(password, method='pbkdf2:sha256'), "points": 10}  # 初始积分10
    save_users(users)
    response = jsonify({'message': 'Registration successful'})
    response.set_cookie('username', username, httponly=False)
    response.set_cookie('points', '10', httponly=False)
    return response, 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    users = load_users()

    if username not in users or not check_password_hash(users[username]['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 400

    response = jsonify({'message': 'Login successful', 'username': username, 'points': users[username]['points']})
    response.set_cookie('username', username, httponly=False)
    response.set_cookie('points', str(users[username]['points']), httponly=False)
    return response, 200

# 主页和文件服务
@app.route('/')
def index():
    return send_from_directory(app.root_path, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory(app.root_path, path)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(os.path.join(app.root_path, 'static'), path)

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, host='0.0.0.0', port=5000)
