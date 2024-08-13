import os
import time
import base64
import collections
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openai import OpenAI, OpenAIError, BadRequestError
import json
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePrecreateModel import AlipayTradePrecreateModel
from alipay.aop.api.request.AlipayTradePrecreateRequest import AlipayTradePrecreateRequest
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# Flask应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # 为Flask会话设置SECRET_KEY
CORS(app)

# 配置上传目录
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'ZEROESSAY', 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
USER_DATA_FILE = os.path.join(app.root_path, 'storage', 'users.json')

# OpenAI 配置，通过环境变量设置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-GZL9qLZUC1WwzLQJ5cE2A0E874B74591BdCcAf83CdE20074")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.xiaoai.plus/v1")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 支付宝配置
ALIPAY_APP_ID = "2021004166659076"
ALIPAY_PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEArUZxwR6/Kpbx3JrYIxleuye7azALdC7AMI4+vfKbfIOWFFE8
kXWL6cxf6yhtIBwUGq3T2SX+1dBJ2p9s8aDU91fvJEoCXcKk66Oue2Bl7MYoTFlf
zSkEabHtmRsx0a/T09KOKAfAf9hzdu/JB/S/ICjARoKBSDpdbIO56ktZZYuETCzS
tzTYqigHtUT+eie2yFxEZ/WDucqBjQeQ2XahfO+b1AK0jE+atmptH6xQroh+PHua
To113O9JJuRX8VMYZiPczxqrxO58lEjSmAOKZfbdCZIhNd5kHKKjIPB4Zzqe6V8T
mpdtt7Rl9x6uF9m1Ke9F3GSspfKvnhTxBtZewIDAQABAoIBAQCtfHr9u4J8MJ8V
dmFgN8t5VX0rzBhZaVVEqjCj1p5NmJ1/J9BYIN5ovZmq2ibOeYwD9gbKNh2sZhnZ
7ynmb5prDS5By1hoX/1uLZY70nYzFd0rDhs5HQNViKhk4hP2xEZgC0blEdOSPEYo
pAlGk2/Dy2yZc9XsRpoTYFyPwbDx36Gu/bR9X5zTc9p+M7QmVjAajdb13Xj1zZBz
knQJ5JJ9Z76r62fbU/8A+htqC6PoAMZp2YN8C4a9ECGZfbQIM7u4EG+OtViHP70h
tTk8Bh5nPmOhMoMbsL65A5Ov13R6FL04VYYnwvFk9i1ErIcGs+v3TLf+qRODBt7V
TuAaErhZAoGBANqNVkDQ8bFMyv0RneXuvf+KblOSdZeq+kXG4ugfSG2thTrJoU8m
5jNdFRmTVmZj9M4to0MmVOAs09fOxaD1iqL8ycGyPBxFQbVjFQId/hRKw7OXuNyS
AwfYSP5H3dAKc7ozZMCsTYuikOf96uVeLrZ98Pb1+n5h7OSQfnd0ZK7tAoGBAK2e
m6P/NQEkUTL7MHDklXvYSo3XHctZQAv4zxbsT6cEMyx0NiUm7so6dKPhFrCaOdiF
5M4ekR9UMo6vSMuFC5JH5dJmkK8BvvYF4UThgQFzNhjQDWyaezjXogInu2omWQ5b
CzrKPx3Nqvll+Vb5+jZRNSD0ZG/8o1KpF3pXpsI/AoGAZ4bNTVv8vATlkGQ6mKr+
u01EmmTpmD8zF9KYI2FO0VqVX32jaYPFVBFuIXHbqJhFEbftAOcdKw4G0CRlIKpj
K5LSZ3Ep0gViTzMNdTPEbbdBX1eU2p8gNDndW6XpCwLSkwJPa4x5rrD9PLOVm5wU
kl+0QFzn11TqCPXf4F8jskECgYBUcMzPTvOOGz6LTFGxkFw7bfsfARFbAP27mcOT
Ai8LhNHYjIhWfGevCUHG7nEp4mCFblXwhFb9CpxLkCpm38Kp89ouPAFgHWe3Axbt
d3M6oEuF32ayPFux7iSVccPGkT7QWkCZOMWPrINXri6zCPRIc1mVp1tLZEVwhFF5
dTKdcQKBgQDYnayVEGlhyc/VatylMBjOgEbphb3A5dvP8OEuY1MbHbDRRBVCF4XH
p0Z2bgrB/BJd2v0b29dMCBSqHK7psWDMNx75ZBLMxFytJS3RUL3h5c9RDGR4uFdL
GVmK8Z4Bx29/xGZ2kt39DzNHUJv2YfFeQnWR5mebUKvlOAfEBXOP0Q==
-----END RSA PRIVATE KEY-----
"""
ALIPAY_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAirUZxwR6/Kpbx3JrYIxleuye7azALdC7AMI4+vfKbfIOWFFE8kXWL6cxf6yhtIBwUGq3T2SX+1dBJ2p9s8aDU91fvJEoCXcKk66Oue2Bl7MYoTFlfzSkEabHtmRsx0a/T09KOKAfAf9hzdu/JB/S/ICjARoKBSDpdbIO56ktZZYuETCzStzTYqigHtUT+eie2yFxEZ/WDucqBjQeQ2XahfO+b1AK0jE+atmptH6xQroh+PHuaTo113O9JJuRX8VMYZiPczxqrxO58lEjSmAOKZfbdCZIhNd5kHKKjIPB4Zzqe6V8Tmpdtt7Rl9x6uF9m1Ke9F3GSspfKvnhTxBtZewIDAQAB
-----END PUBLIC KEY-----
"""

# 初始化支付宝客户端配置
alipay_client_config = AlipayClientConfig()
alipay_client_config.server_url = "https://openapi.alipay.com/gateway.do"
alipay_client_config.app_id = ALIPAY_APP_ID
alipay_client_config.app_private_key = ALIPAY_PRIVATE_KEY
alipay_client_config.alipay_public_key = ALIPAY_PUBLIC_KEY
alipay_client = DefaultAlipayClient(alipay_client_config)

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

def generate_alipay_qr_code(amount, out_trade_no):
    model = AlipayTradePrecreateModel()
    model.out_trade_no = out_trade_no
    model.total_amount = str(amount)
    model.subject = "充值服务"  # 描述信息
    request = AlipayTradePrecreateRequest(biz_model=model)
    response = alipay_client.execute(request)

    if response.is_success():
        return response.qr_code  # 返回支付二维码的URL
    else:
        return None

@app.route('/generate_qr_code', methods=['POST'])
def generate_qr_code():
    data = request.json
    amount = data.get('amount')
    username = data.get('username')

    if amount not in [5, 9, 19]:
        return jsonify({'error': 'Invalid amount'}), 400

    out_trade_no = f"{username}_{int(time.time())}"  # 生成唯一订单号

    qr_code_url = generate_alipay_qr_code(amount, out_trade_no)
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
    response.set_cookie('username', username, httponly=False)  # 修改为httponly=False，以便前端可以访问
    response.set_cookie('points', '1', httponly=False)  # 修改为httponly=False，以便前端可以访问
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
    response.set_cookie('username', username, httponly=False)  # 修改为httponly=False，以便前端可以访问
    response.set_cookie('points', str(users[username]['points']), httponly=False)  # 修改为httponly=False，以便前端可以访问
    return response, 200

@app.route('/upload', methods=['GET', 'POST'])
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
        unique_filename = f"{username}_{int(time.time())}_{filename}"  # 生成唯一文件名
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

    if not filepath and not text_essay:
        return jsonify({'error': 'No valid file or text provided'}), 400

    # 将文件路径和文本一起发送给API处理
    result = process_uploaded_content(filepath, text_essay)

    users[username]['points'] -= 1
    save_users(users)

    response = jsonify({'message': 'Upload and processing successful', 'result': result})
    response.set_cookie('points', str(users[username]['points']), httponly=False)  # 修改为httponly=False，以便前端可以访问
    return response, 200

@app.route('/alipay/notify', methods=['POST'])
def alipay_notify():
    data = request.form.to_dict()
    sign = data.pop('sign', None)

    # 验证支付宝签名
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
    # 把待验证的参数按 key 的字母顺序排序
    sorted_items = sorted(data.items())
    # 构造签名内容字符串
    message = "&".join(f"{k}={v}" for k, v in sorted_items)

    # 载入支付宝公钥
    public_key = RSA.import_key(ALIPAY_PUBLIC_KEY)

    # 创建SHA256的hash对象
    h = SHA256.new(message.encode('utf-8'))

    # 对base64解码后的签名进行验证
    try:
        pkcs1_15.new(public_key).verify(h, base64.b64decode(sign))
        return True
    except (ValueError, TypeError):
        return False

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
