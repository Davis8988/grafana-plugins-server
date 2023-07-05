from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response
import os
import sys
import datetime 
from time import sleep
from os.path import join as join_path
import zipfile
import logging
import shutil
script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

app = Flask(__name__)


def get_persistent_temp_dir():
    temp_dir = '/tmp' # Unix-like
    if os.name == 'nt':  # Windows
        temp_dir = os.environ.get('TEMP')
    return temp_dir

def prepare_logging_dir(log_file_path):
    log_file_dir = os.path.dirname(log_file_path)
    if os.path.exists(log_file_dir):
        return
    print(f"Creating dir: {log_file_dir}")
    try:
        os.makedirs(log_file_dir, exist_ok=True)
    except Exception as e:
        print(f'Error while attempting to create logs dir: {log_file_dir}')
        print(f'{str(e)}')
        raise Exception(f'Failed to create logs dir: "{log_file_dir}" - {str(e)}')

log_file_path            = os.environ.get('LOG_FILE', join_path(script_directory, "logs", "app.log"))
grafana_plugins_dir      = os.environ.get('GRAFANA_PLUGINS_DIR', join_path(script_directory, "grafana_plugins"))
temp_grafana_plugins_dir = join_path(os.environ.get('TEMP_GRAFANA_PLUGINS_DIR', get_persistent_temp_dir()), "grafana_plguins")


# Configure app settings
app.config['GRAFANA_PLUGINS_DIR'] = grafana_plugins_dir
app.config['ALLOWED_EXTENSIONS']  = {'zip'}



# Set up logging
prepare_logging_dir(log_file_path)
log_level = os.environ.get('LOG_LEVEL', logging.INFO)
logging.basicConfig(
    level=log_level,
    format=' %(name)s :: %(levelname)-5s :: %(message)s',  # Updated logging format
    handlers=[
        logging.FileHandler(log_file_path),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
def index():
    logging.info('Accessed main dashboard page')
    directories = os.listdir(app.config['GRAFANA_PLUGINS_DIR'])
    return render_template('index.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/plugins', methods = ['GET'])
def plugins_page():
    logging.info('Accessed plugins page')
    directories = os.listdir(app.config['GRAFANA_PLUGINS_DIR'])
    return render_template('plugins_page.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/create_directory', methods=['POST'])
def create_directory():
    directory_name = request.form['directory_name']
    directory_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    os.makedirs(directory_path, exist_ok=True)
    logging.info(f'Created directory: {directory_name}')
    return redirect(url_for('index'))




def flask_logger():
    """reads logging information"""
    with open(log_file_path) as f:
        while True:
            yield f.read()
            sleep(1)
    # Create empty logfile, old logging will be deleted
    open(log_file_path, 'w').close()

@app.route("/log_stream", methods=["GET"])
def stream():
    """returns logging information"""
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


def search_plugin_json(file_list):
    logging.info(f'Searching for "plugin.json" file in given zip')
    for file in file_list:
        if file.endswith('/plugin.json'):
            return file
    return None


def save_file_in_dir(file, dir_path):
    file_name = file.filename
    logging.info(f'Saving file: {file_name} at: {dir_path}')
    create_dir(dir_path)
    path_to_save_at = join_path(dir_path, file_name)
    if os.path.exists(path_to_save_at):
        logging.info(f'File already exists: {path_to_save_at} - attempting to remove it..')
        try:
            os.remove(path_to_save_at)
        except Exception as e:
            logging.info(f'Failed to remove already existing file: {path_to_save_at} ')
            logging.error(f'Error while removing existing file: {str(e)}')
            return f'Error: Failed to remove existing file: {path_to_save_at}'
        if os.path.exists(path_to_save_at):
            logging.error(f'Even after removing existing file: "{path_to_save_at}" it still exists - Failed to remove already existing file: {path_to_save_at}')
            return f'Error: Even after removing existing file: "{path_to_save_at}" it still exists - Failed to remove already existing file: {path_to_save_at}'
        logging.info(f'Success removing old file: {path_to_save_at}')
    try:
        logging.info(f'Attempting to save file: {file_name} at: {dir_path}')
        file.save(path_to_save_at)
        logging.info(f'File saved: {file.filename}')
    except Exception as e:
        logging.error(f'Error while saving file: {str(e)}')
        return f'Error: Failed to save file: {file.filename} at: {path_to_save_at}'
    return path_to_save_at

def create_dir(dir_path):
    if os.path.exists(dir_path):
        return
    logging.info(f'Creating dir: {dir_path}')
    try:
        os.makedirs(dir_path)
        if not os.path.exists(dir_path):
            raise Exception(f'Even after creating dir: "{dir_path}" it is still missing or unreachable - Failed to create dir: {dir_path}')
    except Exception as e:
        logging.error(f'Error creating dir: {dir_path}')
        logging.error(f'{str(e)}')
        raise Exception(f'Error creating dir: {str(e)}')
    logging.info(f'Success creating dir: {dir_path}')
    
def validate_uploaded_zip_file(zip_file_path):
    logging.info(f'Validating uploaded zip file: {zip_file_path}')
    if not file_exists(zip_file_path):
        logging.error(f'Missing or unreachable uploaded zip file: {zip_file_path} - cannot validate it')
        raise Exception(f'Missing or unreachable uploaded zip file: {zip_file_path} - cannot validate it')
    print_zip_file_containing_files(zip_file_path)
    get_plugins_json_file_path_from_zip_file(zip_file_path)

def print_zip_file_containing_files(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Check if plugin.json exists in the zip file
        file_list = zip_ref.namelist()
        logging.info(f'Listing files under uploaded zip: {zip_file}')
        for x in file_list:
            logging.info(f' - {x}')

def get_plugins_json_file_path_from_zip_file(zip_file):
    plugin_json_file_path = None
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Check if plugin.json exists in the zip file
        file_list = zip_ref.namelist()

        # Search for plugin.json recursively
        plugin_json_file_path = search_plugin_json(file_list)
    if not plugin_json_file_path:
        raise Exception(f'"plugin.json" not found in the uploaded zip file: {zip_file}')
    return plugin_json_file_path

def file_exists(file_path):
    return os.path.exists(file_path)

def delete_file(file_path):
    if not file_exists(file_path):
        return
    logging.info(f'Removing file: {file_path}')
    try:
        os.remove(file_path)
        if file_exists(file_path):
            raise Exception( f'Even after removing the file: "{file_path}" it still exists')
    except Exception as e:
        logging.error(f'Error while removing existing file: {file_path}')
        logging.error(f'{str(e)}')
        raise Exception(f'Error: Failed to remove existing file: {path_to_save_at}')
    logging.info(f'Success removing file: {file_path}')
    
def copy_file(src_file, dest_file):
    logging.info(f'Copying file: {src_file} to: {dest_file}')
    if not file_exists(src_file):
        logging.error(f'Missing or unreachable src file to copy: {src_file} - cannot copy it to: {dest_file}')
        raise Exception(f'Missing or unreachable src file to copy: {src_file} - cannot copy it to: {dest_file}')
    if file_exists(dest_file):
        delete_file(dest_file)
    try:
        shutil.copyfile(src_file, dest_file)
    except Exception as e:
        logging.error(f'Error - Failed to copy file: {src_file} to: {dest_file}')
        logging.error(f'{str(e)}')
        raise Exception(f'Error: Failed to copy file: {src_file} to: {dest_file}')
    # Validate
    if not file_exists(dest_file):
        logging.error(f'Even after copying file: {src_file} to: {dest_file} it is still missing or unreachable')
        raise Exception(f'Even after copying file: {src_file} to: {dest_file} it is still missing or unreachable')
    logging.info(f'Success copying file: {src_file} to: {dest_file}')
    
def copy_zip_file_to_plugins_dir(zip_file_path, plugins_dir):
    create_dir(plugins_dir)
    zip_file_name      = get_file_name_from_path(zip_file_path)
    dest_zip_file_path = join_path(plugins_dir, zip_file_name)
    copy_file(zip_file_path, dest_zip_file_path)
    return dest_zip_file_path

def get_file_name_from_path(file_path):
    # if not file_exists(file_path):
        # logging.error(f'Missing or unreachable file path: {file_path} - cannot get its name')
        # raise Exception(f'Missing or unreachable file path: {file_path} - cannot get its name')
    return os.path.basename(file_path)

def extract_file_from_zip_to_dir(src_zip_file, file_to_extract, dest_dir_to_extract_to):
    logging.info(f'Extracting {file_to_extract} from: {src_zip_file} to: {dest_dir_to_extract_to}')
    extract_file_name = get_file_name_from_path(file_to_extract)
    dest_file_path = join_path(dest_dir_to_extract_to, extract_file_name)
    delete_file(dest_file_path)  # Remove old file if it already exists..
    with zipfile.ZipFile(src_zip_file, 'r') as zip_ref:
        zip_ref.extract(file_to_extract, path=dest_dir_to_extract_to)
    logging.info(f'Success extracting {file_to_extract} from: {src_zip_file} to: {dest_dir_to_extract_to}')
    

def remove_directory_with_content(dir_path):
    logging.info(f'Removing directory with its content: {dir_path}')
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            if os.path.exists(dir_path):
                raise Exception(f'Even after removing the directory: "{dir_path}" it still exists')
        except Exception as e:
            logging.error(f'Error while removing the directory: {dir_path}')
            logging.error(f'{str(e)}')
            raise Exception(f'Error: Failed to remove the directory: {dir_path}')
        logging.info(f'Success removing the directory with its content: {dir_path}')

@app.route('/remove/<path:file_or_dir_path>', methods=['GET'])
def remove_file_or_dir(file_or_dir_path):
    path_to_remove = join_path(app.config['GRAFANA_PLUGINS_DIR'], file_or_dir_path)
    logging.info(f'Removing: {path_to_remove}')
    if not file_exists(path_to_remove):
        return f'Error: File or directory not found: {path_to_remove}'

    if os.path.isfile(path_to_remove):
        # It's a file
        delete_file(path_to_remove)
        logging.info(f'Removed file: {path_to_remove}')
    else:
        # It's a directory
        remove_directory_with_content(path_to_remove)
        logging.info(f'Removed directory: {path_to_remove}')
    
    return redirect(url_for('index'))

@app.route('/remove_directory', methods=['POST'])
def remove_directory():
    directory_name = request.form['directory_name']
    directory_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    remove_directory_with_content(directory_path)
    logging.info(f'Removed directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/remove_file', methods=['POST'])
def remove_file():
    directory_name = request.form['directory_name']
    file_name = request.form['file_name']
    file_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name, file_name)
    delete_file(file_path)
    logging.info(f'Removed file: {file_name} from directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/download/<path:path>')
def download_file(path):
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    return send_from_directory(os.path.join(app.config['GRAFANA_PLUGINS_DIR'], directory), filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload():
    directory_name = request.form.get('directory', None)
    file = request.files['file']
    if not directory_name:
        error_message = f'Error uploading: "{file.filename}" - Invalid directory: "{directory_name}". Please choose a directory from the list or create one if non is existing..'
        logging.error(error_message)
        return error_message
    if not file or not allowed_file(file.filename):
        error_message = f'Error uploading: "{file.filename}" - Invalid file or file type not allowed'
        logging.error(error_message)
        return error_message

    # Save the uploaded file into a temp dir first..
    temp_uploaded_file_path = save_file_in_dir(file, temp_grafana_plugins_dir)
    
    # Validate uploaded zip file:
    validate_uploaded_zip_file(temp_uploaded_file_path)
    
    
    directory_path       = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    copied_zip_file_path = copy_zip_file_to_plugins_dir(temp_uploaded_file_path, directory_path)
    file_path            = copied_zip_file_path
    
    plugin_json_file_path = get_plugins_json_file_path_from_zip_file(file_path)
    
    try:
        extract_file_from_zip_to_dir(file_path, plugin_json_file_path, directory_path)
        logging.info(f'Success uploading and extracting file: {file.filename}')
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


def prepare_grafana_plugins_dir(dir_path):
    logging.info(f'Preparing grafana plugins dir at: {dir_path}')
    create_dir(dir_path)

if __name__ == '__main__':
    prepare_grafana_plugins_dir(grafana_plugins_dir)
    app.run(debug=True, port=3011) 
