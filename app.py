from flask import Flask, render_template, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'E:/eeeee'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services.html')
def services():
    return render_template('services.html')

@app.route('/upload.html')
def upload():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    if 'essay' in request.files:
        essay = request.files['essay']
        essay.save(os.path.join(UPLOAD_FOLDER, essay.filename))
        
    if 'text_essay' in request.form:
        text_essay = request.form['text_essay']
        with open(os.path.join(UPLOAD_FOLDER, 'text_essay.txt'), 'w') as f:
            f.write(text_essay)
            
    return 'Upload successful!'

if __name__ == '__main__':
    app.run(debug=True)
