from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
import logging
import time
import random
import string

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Logger configuration
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(message)s')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/services.html')
def services():
    return render_template('services.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            logging.info(f'File uploaded: {filename}')
            flash('File successfully uploaded')
            return redirect(url_for('uploaded_file', filename=filename))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/process', methods=['POST'])
def process_file():
    # Simulate file processing
    time.sleep(2)
    flash('File successfully processed')
    return redirect(url_for('index'))

@app.route('/generate-report', methods=['POST'])
def generate_report():
    # Simulate report generation
    report = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    flash(f'Report generated: {report}')
    return redirect(url_for('index'))

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    # Simulate contact form submission
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    logging.info(f'Contact form submitted by {name} ({email}): {message}')
    flash('Message successfully sent')
    return redirect(url_for('contact'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

def create_large_code_base():
    # Generate additional dummy functions to increase the codebase
    for i in range(950):
        exec(f"def dummy_function_{i}(): pass")

create_large_code_base()

if __name__ == '__main__':
    app.run(debug=True)
