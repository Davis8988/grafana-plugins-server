from flask import Flask, render_template, request, redirect, url_for
import os
import zipfile

app = Flask(__name__)

# Configure app settings
app.config['UPLOAD_FOLDER']      = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    directories = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', directories=directories)

@app.route('/create_directory', methods=['POST'])
def create_directory():
    directory_name = request.form['directory_name']
    directory_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_name)
    os.makedirs(directory_path, exist_ok=True)
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    directory_name = request.form['directory']
    file = request.files['file']
    if file and allowed_file(file.filename):
        directory_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_name)
        file.save(os.path.join(directory_path, file.filename))
        with zipfile.ZipFile(os.path.join(directory_path, file.filename), 'r') as zip_ref:
            zip_ref.extract('plugin.json', path=directory_path)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=3011) 
