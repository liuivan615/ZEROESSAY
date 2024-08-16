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
app.config['SECRET_KEY'] = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})

# 配置上传目录
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'ZEROESSAY', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')

# OpenAI 配置，通过环境变量设置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-GZL9qLZUC1WwzLQJ5cE2A0E874B74591BdCcAf83CdE20074")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.xiaoai.plus/v1")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 支付接口配置
PAY_MERCHANT_ID = "3326"  # 商户ID
PAY_SECRET_KEY = "b361b63f6c4950e726ad6f6ca3e2b07d"  # 商户密钥
PAY_API_URL = "https://pay.yzhifupay.com/"  # 支付API地址
NOTIFY_URL = "http://47.99.81.13:5000/yipay_notify"  # 异步通知地址
RETURN_URL = "http://47.99.81.13:5000/return_url"  # 同步返回地址

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 读取用户数据的函数
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

# 保存用户数据的函数
def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f)

# 图片处理与API调用相关函数
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

        # 打印API的完整响应
        print("OpenAI API 响应内容：", result)

        return result
    except (BadRequestError, OpenAIError) as e:
        print("OpenAI API 错误：", e)
        return handle_api_error(e)

def analyze_generate_essay(ocr_text, base64_text, user_input_text):
    combined_text = f"OCR 识别结果: {ocr_text}\n\nBase64 识别结果: {base64_text}\n\n用 户输入文本: {user_input_text}"
    prompt = f"""
    根据以下提供的图片和文本信息，从OCR识别内容中提取出雅思作文的题目和正文。题目需要中英文表达，作文不添加额外信息，只选取与题目和作文相关的部分。

    提供的内容：
    {combined_text[:1500]}
    """

    analysis_result = process_text_with_gpt(combined_text, prompt)
    return analysis_result

def process_uploaded_content(image_path, user_input_text):
    ocr_text = extract_text_with_ocr(image_path) if image_path else ""
    base64_text = get_image_base64(image_path) if image_path else ""

    analysis_result = analyze_generate_essay(ocr_text, base64_text, user_input_text)

    # 打印分析结果，调试API是否返回有效数据
    print("API 返回的分析结果：", analysis_result)

    return analysis_result

# 上传文件处理的API端点
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    # 检查是否有文件上传或文本上传
    file = request.files.get('file')  # 获取文件（如果有）
    text_essay = request.form.get('text_essay')  # 获取文本（如果有）

    # 如果既没有文件也没有文本，则返回错误
    if not file and not text_essay:
        print("No file or text part in the request")
        return jsonify({'error': 'No file or text part in the request'}), 400

    # 初始化文件路径为 None
    filepath = None

    # 如果上传了文件，则处理文件
    if file and file.filename != '':
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"Saving file to {filepath}")
            file.save(filepath)
        else:
            print("Invalid file")
            return jsonify({'error': 'Invalid file'}), 400

    # 处理上传内容：无论是文件、文本或两者
    result = process_uploaded_content(filepath, text_essay)

    # 更新用户积分 (假设已经有相关用户登录并获取了用户名)
    users = load_users()
    username = request.cookies.get('username')
    if username and username in users:
        users[username]['points'] -= 1
        save_users(users)
        response = jsonify({'redirect': f'/report?result={result}'})
        response.set_cookie('points', str(users[username]['points']), httponly=False)
    else:
        response = jsonify({'redirect': f'/report?result={result}'})

    print("Upload and processing successful")

    # 返回成功并跳转到报告页面
    return response, 200

# 报告页面的路由，用于显示处理结果
@app.route('/report')
def report():
    # 从GET参数中获取处理结果
    result = request.args.get('result', None)

    # 如果有结果，将其转化为字典
    if result:
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = None

    # 如果没有结果，提示重新上传
    if not result:
        result = {
            "titleEn": "No result",
            "titleZh": "没有可显示的结果，请重新上传文件或文本进行处理。",
            "scores": {
                "taskAchievement": 0,
                "coherenceCohesion": 0,
                "lexicalResource": 0,
                "grammaticalRange": 0,
                "overall": 0,
            },
            "feedback": [],
            "finalEssay": "No essay available."
        }

    # 渲染 report.html 并传递结果到前端
    return render_template('report.html', result=result)

# 支付接口生成订单
def generate_pay_order(amount, out_trade_no, notify_url, return_url, payment_type='alipay'):
    params = {
        "pid": PAY_MERCHANT_ID,
        "type": payment_type,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "return_url": return_url,
        "name": "充值服务",
        "money": str(amount),
        "sign_type": "MD5"
    }

    # 按照参数名的ASCII码排序，并且排除掉sign和sign_type
    sign_str = '&'.join([f"{key}={params[key]}" for key in sorted(params) if key != 'sign' and key != 'sign_type' and params[key]]) + PAY_SECRET_KEY
    print(f"签名前的字符串: {sign_str}")  # 打印签名前的字符串

    # 生成签名
    params["sign"] = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    print(f"生成的MD5签名: {params['sign']}")  # 打印生成的签名

    try:
        # 发送POST请求
        response = requests.post(PAY_API_URL, data=params)
        print("Response status code:", response.status_code)
        print("Response content:", response.text)

        # 如果响应成功且返回HTML页面
        if response.status_code == 200 and '<html>' in response.text:
            return response.url  # 返回支付页面URL
        else:
            print(f"支付请求错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error during Pay order generation: {e}")
        return None

@app.route('/generate_qr_code', methods=['POST'])
def generate_qr_code():
    data = request.json
    amount = data.get('amount')
    username = data.get('username')

    if amount not in [5, 9, 19, 29, 59]:
        return jsonify({'error': 'Invalid amount'}), 400

    out_trade_no = f"{username}_{int(time.time())}"  # 生成唯一订单号

    # 使用IP地址作为通知地址和返回地址
    notify_url = NOTIFY_URL
    return_url = RETURN_URL

    qr_code_url = generate_pay_order(amount, out_trade_no, notify_url, return_url)
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

@app.route('/yipay_notify', methods=['POST'])
def yipay_notify():
    data = request.form.to_dict()
    sign = data.pop('sign', None)

    # 验证支付签名
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
    message = "&".join(f"{k}={v}" for k, v in sorted_items if v and k != 'sign') + PAY_SECRET_KEY
    calculated_sign = hashlib.md5(message.encode('utf-8')).hexdigest()
    return calculated_sign == sign

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
