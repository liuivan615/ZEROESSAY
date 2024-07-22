from flask import Flask, request, render_template, jsonify
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': '没有文件上传'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': '没有选择文件'}), 400

    if file:
        # 保存文件到服务器
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        # 处理文件（图片OCR或直接读取文字）
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = pytesseract.image_to_string(Image.open(file_path))
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        # 将内容复制粘贴到GPT程序中
        gpt_response = process_with_gpt(text)

        # 返回批改结果
        return jsonify({'message': gpt_response})

def process_with_gpt(text):
    # 在这里实现将text粘贴到GPT程序并获取结果的逻辑
    # 假设我们直接调用一个本地的GPT程序并返回结果
    return "批改后的结果"

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
