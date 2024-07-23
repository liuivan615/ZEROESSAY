from flask import Flask, request, render_template, redirect, url_for
import os

app = Flask(__name__)

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle file upload
        if 'essay' in request.files:
            file = request.files['essay']
            if file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)

        # Handle text essay
        if 'text_essay' in request.form:
            text_essay = request.form['text_essay']
            if text_essay != '':
                text_path = os.path.join(app.config['UPLOAD_FOLDER'], 'text_essay.txt')
                with open(text_path, 'w') as text_file:
                    text_file.write(text_essay)
        
        return redirect(url_for('index'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
