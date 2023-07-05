from modules import global_config
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response
import os
import sys
import datetime 
from time import sleep
from os.path import join as join_path
import zipfile
import logging
import shutil
from modules import helpers
script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

app = Flask(__name__)
global_config.app = app

log_file_path            = os.environ.get('LOG_FILE', join_path(script_directory, "logs", "app.log"))
grafana_plugins_dir      = os.environ.get('GRAFANA_PLUGINS_DIR', join_path(script_directory, "grafana_plugins"))
temp_grafana_plugins_dir = join_path(os.environ.get('TEMP_GRAFANA_PLUGINS_DIR', helpers.get_persistent_temp_dir()), "grafana_plguins")

global_config.log_file_path            = log_file_path
global_config.grafana_plugins_dir      = grafana_plugins_dir
global_config.temp_grafana_plugins_dir = temp_grafana_plugins_dir


# Configure app settings
app.config['GRAFANA_PLUGINS_DIR'] = grafana_plugins_dir
app.config['ALLOWED_EXTENSIONS']  = {'zip'}

# Prepare env:
helpers.prepare_logging_dir(log_file_path)
helpers.prepare_grafana_plugins_dir(grafana_plugins_dir)

# Set up logging
log_level = os.environ.get('LOG_LEVEL', logging.INFO)
logging.basicConfig(
    level=log_level,
    format=' %(name)s :: %(levelname)-5s :: %(message)s',  # Updated logging format
    handlers=[
        logging.FileHandler(log_file_path),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)


@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
def index():
    logging.info('Accessed main dashboard page')
    directories = os.listdir(app.config['GRAFANA_PLUGINS_DIR'])
    return render_template('index.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/plugins/list', methods = ['GET'])
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




@app.route("/log_stream", methods=["GET"])
def stream():
    """returns logging information"""
    return Response(helpers.flask_logger(), mimetype="text/plain", content_type="text/event-stream")


    
@app.route('/remove/<path:file_or_dir_path>', methods=['GET'])
def remove_file_or_dir(file_or_dir_path):
    path_to_remove = join_path(app.config['GRAFANA_PLUGINS_DIR'], file_or_dir_path)
    logging.info(f'Removing: {path_to_remove}')
    if not helpers.file_exists(path_to_remove):
        return f'Error: File or directory not found: {path_to_remove}'

    if os.path.isfile(path_to_remove):
        # It's a file
        helpers.delete_file(path_to_remove)
        logging.info(f'Removed file: {path_to_remove}')
    else:
        # It's a directory
        helpers.remove_directory_with_content(path_to_remove)
        logging.info(f'Removed directory: {path_to_remove}')
    
    return redirect(url_for('index'))

@app.route('/remove_directory', methods=['POST'])
def remove_directory():
    directory_name = request.form['directory_name']
    directory_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    helpers.remove_directory_with_content(directory_path)
    logging.info(f'Removed directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/remove_file', methods=['POST'])
def remove_file():
    directory_name = request.form['directory_name']
    file_name = request.form['file_name']
    file_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name, file_name)
    helpers.delete_file(file_path)
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
    if not file or not helpers.allowed_file(file.filename):
        error_message = f'Error uploading: "{file.filename}" - Invalid file or file type not allowed. Only "*.zip" files are allowed'
        logging.error(error_message)
        return error_message

    # Save the uploaded file into a temp dir first..
    temp_uploaded_file_path = helpers.save_file_in_dir(file, temp_grafana_plugins_dir)
    
    # Validate uploaded zip file:
    helpers.validate_uploaded_zip_file(temp_uploaded_file_path)
    
    
    directory_path       = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    copied_zip_file_path = helpers.copy_zip_file_to_plugins_dir(temp_uploaded_file_path, directory_path)
    file_path            = copied_zip_file_path
    
    plugin_json_file_path = helpers.get_plugins_json_file_path_from_zip_file(file_path)
    
    try:
        helpers.extract_file_from_zip_to_dir(file_path, plugin_json_file_path, directory_path)
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


if __name__ == '__main__':
    app.run(debug=True, port=3011) 
