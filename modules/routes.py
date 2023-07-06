from modules import runtime_config
from modules import helpers
from flask import render_template, request, redirect, url_for, send_from_directory, Response
import os
from os.path import join as join_path
import zipfile
import logging

app = runtime_config.app
temp_grafana_plugins_dir = runtime_config.temp_grafana_plugins_dir


@app.route('/')
@app.route('/index', methods = ['GET', 'POST'])
def index():
    logging.info('Accessed main dashboard page')
    grafana_plugins_directory = app.config['GRAFANA_PLUGINS_DIR']
    directories = [ name for name in os.listdir(grafana_plugins_directory) if os.path.isdir(os.path.join(grafana_plugins_directory, name)) ]  # Get only dirs
    return render_template('index.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/plugins', methods = ['GET'])
def plugins_page():
    logging.info('Accessed plugins page')
    grafana_plugins_directory = app.config['GRAFANA_PLUGINS_DIR']
    directories = [ name for name in os.listdir(grafana_plugins_directory) if os.path.isdir(os.path.join(grafana_plugins_directory, name)) ]  # Get only dirs
    return render_template('plugins_page.html', 
                            directories=directories,
                            os=os,
                            app=app)

# @app.route('/create_directory', methods=['POST'])
# def create_directory():
#     directory_name = runtime_config.repo_name
#     directory_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
#     os.makedirs(directory_path, exist_ok=True)
#     logging.info(f'Created directory: {directory_name}')
#     return redirect(url_for('index'))




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
    directory_name = runtime_config.repo_name
    directory_path = join_path(app.config['GRAFANA_PLUGINS_DIR'], directory_name)
    helpers.remove_directory_with_content(directory_path)
    logging.info(f'Removed directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/remove_file', methods=['POST'])
def remove_file():
    directory_name = runtime_config.repo_name
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
    directory_name = runtime_config.repo_name
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
