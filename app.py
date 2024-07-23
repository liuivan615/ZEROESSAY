from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# 配置上传文件路径
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传文件夹存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/services.html')
def services():
    return render_template('services.html')

@app.route('/upload.html')
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'essay' in request.files:
        essay = request.files['essay']
        essay.save(os.path.join(app.config['UPLOAD_FOLDER'], essay.filename))
    if 'text_essay' in request.form:
        text_essay = request.form['text_essay']
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'text_essay.txt'), 'w') as f:
            f.write(text_essay)
    return 'Upload successful!'

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
