import os
import time
import base64
import collections
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openai import OpenAI, OpenAIError, BadRequestError
import json
import hashlib

# Flask应用初始化
app = Flask(__name__)
CORS(app)

# 配置上传目录
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'ZEROESSAY', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.xiaoai.plus/v1")

# 初始化OpenAI客户端
client = OpenAI(api_key=api_key, base_url=base_url)

# 指定Tesseract的安装路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 上下文内存，用于保持对话上下文
context_memory = collections.deque(maxlen=15)

def update_context(new_message):
    context_memory.append(new_message)

def get_context():
    return " ".join(context_memory)

def handle_api_error(e):
    error_detail = str(e)
    return f"遇到了一些问题，请稍后再试。详细信息: {error_detail}"

def clean_path(path):
    return path.strip().strip('"').replace('\\\\', '\\').replace('\\\\"', '\\')

def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    image = image.point(lambda x: 0 if x < 140 else 255, '1')
    image = image.filter(ImageFilter.MedianFilter())
    return image

def extract_text_with_ocr(image_path):
    try:
        preprocessed_image = preprocess_image(image_path)
        text = pytesseract.image_to_string(preprocessed_image)
        return text.strip()
    except Exception as e:
        return f"Error performing OCR on the image: {str(e)}"

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        return None

def process_text_with_gpt(text, prompt=None):
    MAX_TOKENS = 1000  
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": text[:MAX_TOKENS]}
    ]
    
    if prompt:
        messages.append({"role": "user", "content": prompt[:MAX_TOKENS]})
    
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=4096)
        result = response.choices[0].message.content.strip()
        return result
    except (BadRequestError, OpenAIError) as e:
        return handle_api_error(e)

def analyze_generate_essay(ocr_text, base64_text, user_input_text):
    combined_text = f"OCR 识别结果: {ocr_text}\n\nBase64 识别结果: {base64_text}\n\n用户输入文本: {user_input_text}"
    prompt = f"""
    根据以下提供的图片和文本信息，从OCR识别内容中提取出雅思作文的题目和正文。题目需要中英文表达，作文不添加额外信息，只选取与题目和作文相关的部分。

    提供的内容：
    {combined_text[:1500]}

    生成的题目和作文应严格基于OCR识别结果，不得添加额外内容。如果无法识别出题目，请注明"未能识别出题目"。作文部分一定要生成。
    """
    
    analysis_result = process_text_with_gpt(combined_text, prompt)
    return analysis_result

def evaluate_and_improve_essay(essay_text):
    prompt = f"""
    下面是一篇雅思作文，请从以下四个方面进行评分：
    1. 任务回应（Task Achievement/Task Response）
    2. 连贯与衔接（Coherence and Cohesion）
    3. 词汇资源（Lexical Resource）
    4. 语法多样性与准确性（Grammatical Range and Accuracy）
    
    请为每个维度打分并给出评分理由，并直接给出总分。

    作文内容：
    {essay_text[:1000]}
    """
    
    evaluation_result = process_text_with_gpt(essay_text, prompt)
    return evaluation_result

def improve_each_sentence(essay_text):
    prompt = f"""
    以下是雅思作文的原文内容，请根据GPT分析出的缺陷逐句改进这些句子，并解释每个改进的原因。改进后的句子应以英文给出，并以蓝色标记，解释原因则用中文给出，并以红色标记。

    改进后的小作文应不超过150个英文单词，大作文应不超过250个英文单词。

    作文内容：
    {essay_text[:1000]}
    """
    
    improved_essay = process_text_with_gpt(essay_text, prompt)
    return improved_essay

def generate_final_essay(original_essay, improvements):
    prompt = f"""
    请根据以下原始作文和改进建议，生成改进后的完整雅思作文。请确保保留原文的合理部分，并应用改进后的内容。

    原始作文：
    {original_essay[:1000]}

    改进建议：
    {improvements[:1000]}
    """
    
    final_essay = process_text_with_gpt(original_essay, prompt)
    return final_essay

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 定义积分规则
POINTS_RULES = [
    (19, 5),
    (9, 2),
    (5, 1)
]

def calculate_points(amount):
    points = 0
    for threshold, reward in POINTS_RULES:
        if amount >= threshold:
            points += reward
            break
    return points

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
    response = jsonify({'message': 'Login successful', 'username': username, 'points': users[username]['points']})
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
    text_essay = request.form.get('text_essay')
    filepath = None
    
    if file and allowed_file(file.filename):
        # 保存文件
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
    
    if not filepath and not text_essay:
        return jsonify({'error': 'No valid file or text provided'}), 400

    # 将文件路径和文本一起发送给API处理
    result = process_uploaded_content(filepath, text_essay)
    
    users[username]['points'] -= 1
    save_users(users)
    
    response = jsonify({'message': 'Upload and processing successful', 'result': result})
    response.set_cookie('points', str(users[username]['points']), httponly=True)
    return response, 200

@app.route('/alipay/notify', methods=['POST'])
def alipay_notify():
    data = request.form.to_dict()
    sign = data.pop('sign', None)

    # 验证支付宝签名（此处需要使用你的支付宝公钥验证签名）
    if not verify_alipay_signature(data, sign):
        return 'failure', 400
    
    if data.get('trade_status') == 'TRADE_SUCCESS':
        user_id = data.get('out_trade_no')  # 假设你的订单号是用户ID
        amount = float(data.get('total_amount', 0))
        
        # 计算积分
        points = calculate_points(amount)
        
        # 更新用户积分
        users = load_users()
        if user_id in users:
            users[user_id]['points'] += points
            save_users(users)
            return 'success', 200
        else:
            return 'failure', 400
    return 'failure', 400

def verify_alipay_signature(data, sign):
    # 这里应该实现支付宝签名的验证逻辑
    # 例如使用支付宝的公钥和相应的算法来验证
    # 此处是示例，可以使用支付宝提供的SDK或手动实现
    return True

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5000)
