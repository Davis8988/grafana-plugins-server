from flask import Flask, render_template, request, redirect, url_for
import os
import zipfile
import logging

app = Flask(__name__)


def get_persistent_temp_dir():
    temp_dir = '/tmp' # Unix-like
    if os.name == 'nt':  # Windows
        temp_dir = os.environ.get('TEMP')
    return temp_dir

uploads_folder = os.environ.get('UPLOADS_DIR', "uploads")
temp_uploads_folder = os.path.join(os.environ.get('TEMP_UPLOADS_FOLDER', get_persistent_temp_dir()), "grafana-plguins")


# Configure app settings
app.config['UPLOAD_FOLDER']      = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'zip'}

# Set up logging
log_level = os.environ.get('LOG_LEVEL', logging.INFO)
logging.basicConfig(level=log_level)

    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/')
def index():
    logging.info('Accessed main dashboard page')
    directories = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/create_directory', methods=['POST'])
def create_directory():
    directory_name = request.form['directory_name']
    directory_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_name)
    os.makedirs(directory_path, exist_ok=True)
    logging.info(f'Created directory: {directory_name}')
    return redirect(url_for('index'))


def search_plugin_json(zip_ref, file_list):
    logging.info(f'Searching for "plugin.json" file in the uploaded zip')
    for file in file_list:
        if file.endswith('/plugin.json'):
            return file
    return None


def save_file_in_dir(file, path_to_save_at):
    file_name = file.filename
    logging.info(f'Saving file: {file_name} at: {path_to_save_at}')
    if os.path.exists(path_to_save_at):
        logging.info(f'File already exists: {path_to_save_at} - attempting to remove it..')
        try:
            os.remove(path_to_save_at)
        except Exception as e:
            logging.info(f'Failed to remove already existing file: {path_to_save_at} ')
            logging.error(f'Error while removing existing file: {str(e)}')
            return f'Error: Failed to remove existing file: {path_to_save_at}'
    try:
        file.save(path_to_save_at)
        logging.info(f'File saved: {file.filename}')
    except Exception as e:
        logging.error(f'Error while saving file: {str(e)}')
        return f'Error: Failed to save file: {file.filename} at: {path_to_save_at}'

@app.route('/upload', methods=['POST'])
def upload():
    directory_name = request.form['directory']
    file           = request.files['file']
    
    if not file or not allowed_file(file.filename):
        logging.error('Error while uploading file: {file} - Invalid file or file type not allowed')
        return f'Error uploading: "{file.filename}" - Invalid file or file type not allowed'
    
    # Save the uploaded file into a temp dir first..
    temp_file_path = os.path.join(temp_uploads_folder, file.filename)
    save_file_in_dir(file, temp_file_path)
    
    directory_path = os.path.join(app.config['UPLOAD_FOLDER'], directory_name)
    file_path = os.path.join(directory_path, file.filename)
    file.save(file_path)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Check if plugin.json exists in the zip file
            file_list = zip_ref.namelist()
            logging.info(f'Listing files under uploaded zip: {file.filename}')
            for x in file_list:
                logging.info(f' - {x}')
             
             # Search for plugin.json recursively
            plugin_json_file_path = search_plugin_json(zip_ref, file_list)

            if not plugin_json_file_path:
                raise Exception(f'"plugin.json" not found in the uploaded zip file: {file.filename}')


            logging.info(f'Extracting plugin.json: {plugin_json_file_path} to: {directory_path}')
            zip_ref.extract(plugin_json_file_path, path=directory_path)
            logging.info(f'Uploaded and extracted file: {file.filename}')
    except Exception as e:
        # Remove the uploaded file
        os.remove(file_path)
        logging.error(f'Error while uploading file: {str(e)}')

        # Get a list of all files in the zip file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()

        error_message = f'Error: {str(e)}\n'
        error_message += f'Files found in the zip file: {", ".join(file_list)}'

        return error_message

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=3011) 
