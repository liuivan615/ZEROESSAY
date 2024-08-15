import os
import time
import base64
import collections
import hashlib
import requests
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openai import OpenAI, OpenAIError, BadRequestError
import json

# Flask应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # 为Flask会话设置SECRET_KEY
CORS(app)

# 配置上传目录
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'ZEROESSAY', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')

# OpenAI 配置，通过环境变量设置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.xiaoai.plus/v1")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 易支付配置，通过环境变量设置
YIPAY_MERCHANT_ID = os.getenv("YIPAY_MERCHANT_ID", "7200")
YIPAY_SECRET_KEY = os.getenv("YIPAY_SECRET_KEY", "w7r7f7f72I7oO6koB572E6fev672BK9v")
YIPAY_API_URL = os.getenv("YIPAY_API_URL", "https://yi-pay.com/mapi.php")

# 指定Tesseract的安装路径，适配Linux环境
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

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
        response = client.chat.completions.create(model="gpt-4", messages=messages, max_tokens=4096)
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
    请根据以下原始作文和改进建议，生成改进后的完整雅思作文。请确保保留原文的合理部分， 并应用改进后的内容。

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
    (59, 25),
    (29, 10),
    (19, 4),
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

def generate_yipay_order(amount, out_trade_no, notify_url, return_url, payment_type='alipay'):
    params = {
        "pid": YIPAY_MERCHANT_ID,
        "type": payment_type,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "return_url": return_url,
        "name": "充值服务",
        "money": str(amount),
        "sign_type": "MD5"
    }

    # 构造签名
    sign_str = '&'.join([f"{key}={params[key]}" for key in sorted(params) if params[key]]) + YIPAY_SECRET_KEY
    params["sign"] = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    try:
        response = requests.post(YIPAY_API_URL, data=params)
        if response.status_code == 200:
            result = response.json()
            if result['code'] == 1:
                return result.get('payurl') or result.get('qrcode') or result.get('urlscheme')
            else:
                print(f"Yipay response error: {result['msg']}")
                return None
        else:
            print(f"Yipay response error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error during Yipay order generation: {e}")
        return None

@app.route('/simple')
def simple():
    return render_template('simple.html')

@app.route('/generate_qr_code', methods=['POST'])
def generate_qr_code():
    data = request.json
    amount = data.get('amount')
    username = data.get('username')

    if amount not in [5, 9, 19, 29, 59]:
        return jsonify({'error': 'Invalid amount'}), 400

    out_trade_no = f"{username}_{int(time.time())}"  # 生成唯一订单号
    notify_url = "http://www.yourdomain.com/yipay_notify"  # 替换为你的notify_url
    return_url = "http://www.yourdomain.com/return_url"  # 替换为你的return_url

    qr_code_url = generate_yipay_order(amount, out_trade_no, notify_url, return_url)
    if qr_code_url:
        return jsonify({'qr_code_url': qr_code_url}), 200
    else:
        return jsonify({'error': 'Failed to generate QR code'}), 500

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
    users[username] = {"password": generate_password_hash(password, method='pbkdf2:sha256'), "points": 1}
    save_users(users)
    response = jsonify({'message': 'Registration successful'})
    response.set_cookie('username', username, httponly=False)
    response.set_cookie('points', '1', httponly=False)
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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    # 处理上传逻辑
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
        unique_filename = f"{username}_{int(time.time())}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

    if not filepath and not text_essay:
        return jsonify({'error': 'No valid file or text provided'}), 400

    # 处理上传内容
    result = process_uploaded_content(filepath, text_essay)  # 你需要定义这个函数的具体内容

    users[username]['points'] -= 1
    save_users(users)

    response = jsonify({'message': 'Upload and processing successful', 'result': result})
    response.set_cookie('points', str(users[username]['points']), httponly=False)
    return response, 200

@app.route('/yipay_notify', methods=['POST'])
def yipay_notify():
    data = request.form.to_dict()
    sign = data.pop('sign', None)

    # 验证易支付签名
    if not verify_yipay_signature(data, sign):
        return 'failure', 400

    if data.get('trade_status') == 'TRADE_SUCCESS':
        out_trade_no = data.get('out_trade_no')
        amount = float(data.get('money', 0))

        # 计算积分
        points = calculate_points(amount)

        # 更新用户积分
        users = load_users()
        username = out_trade_no.split('_')[0]
        if username in users:
            users[username]['points'] += points
            save_users(users)
            return 'success', 200
        else:
            return 'failure', 400
    return 'failure', 400

def verify_yipay_signature(data, sign):
    sorted_items = sorted(data.items())
    message = "&".join(f"{k}={v}" for k, v in sorted_items if v and k != 'sign') + YIPAY_SECRET_KEY
    calculated_sign = hashlib.md5(message.encode('utf-8')).hexdigest()
    return calculated_sign == sign

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
