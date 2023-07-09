from modules import runtime_config
from modules import helpers
from modules import grafana_plugin_file
from flask import render_template, request, redirect, url_for, send_from_directory, Response, jsonify
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
    grafana_plugins_repo_directory = app.config['GRAFANA_PLUGINS_REPO_DIR']
    directories = [ name for name in os.listdir(grafana_plugins_repo_directory) if os.path.isdir(os.path.join(grafana_plugins_repo_directory, name)) ]  # Get only dirs
    for x in directories:
        logging.info(f"Dir: {x}")
    return render_template('index.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/plugins', methods = ['GET'])
def plugins_page():
    logging.info('Accessed plugins page')
    grafana_plugins_repo_directory = app.config['GRAFANA_PLUGINS_REPO_DIR']
    directories = [ name for name in os.listdir(grafana_plugins_repo_directory) if os.path.isdir(os.path.join(grafana_plugins_repo_directory, name)) ]  # Get only dirs
    return render_template('plugins_page.html', 
                            directories=directories,
                            os=os,
                            app=app)

@app.route('/plugins/repo', methods = ['GET'])
def plugins_repo_page():
    logging.info('Accessed plugins/repo page')
    helpers.calculate_uploaded_plugins_summary_json_file()
    json_data = helpers.read_json_file(runtime_config.grafana_plugins_summary_json_file)
    return jsonify(json_data)

# @app.route('/create_directory', methods=['POST'])
# def create_directory():
#     directory_name = runtime_config.repo_name
#     directory_path = join_path(app.config['GRAFANA_PLUGINS_REPO_DIR'], directory_name)
#     os.makedirs(directory_path, exist_ok=True)
#     logging.info(f'Created directory: {directory_name}')
#     return redirect(url_for('index'))




@app.route("/log_stream", methods=["GET"])
def stream():
    """returns logging information"""
    return Response(helpers.flask_logger(), mimetype="text/plain", content_type="text/event-stream")


    
@app.route('/remove/<path:file_or_dir_path>', methods=['GET'])
def remove_file_or_dir(file_or_dir_path):
    path_to_remove = join_path(app.config['GRAFANA_PLUGINS_REPO_DIR'], file_or_dir_path)
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

@app.route('/remove_file', methods=['POST'])
def remove_file():
    directory_name = runtime_config.repo_name
    file_name = request.form['file_name']
    file_path = join_path(app.config['GRAFANA_PLUGINS_REPO_DIR'], file_name)
    helpers.delete_file(file_path)
    logging.info(f'Removed file: {file_name} from directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/download/<path:path>')
def download_file(path):
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    return send_from_directory(os.path.join(app.config['GRAFANA_PLUGINS_REPO_DIR'], directory), filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if not grafana_plugin_file.validate_uploaded_zip_file(uploaded_file):
        return

    # Save the uploaded file into a temp dir first..
    extract_file_name           = uploaded_file.filename
    file_name_without_extension = os.path.splitext(extract_file_name)[0]
    temp_uploaded_file_path     = helpers.save_file_in_dir(uploaded_file, temp_grafana_plugins_dir)
    temp_plugin_dir             = join_path(temp_grafana_plugins_dir, file_name_without_extension)
    
    # Validate uploaded zip file:
    if not grafana_plugin_file.validate_uploaded_zip_file(uploaded_file):
        return
        
    # Print
    helpers.print_zip_file_containing_files(zip_file_path)
    helpers.get_plugins_json_file_path_from_zip_file(zip_file_path)
    # Extract the zip file to temp dir:
    helpers.extract_zip_to_dir(temp_uploaded_file_path, temp_plugin_dir)
    
    # Read plugin details:
    plugin_json_file_path = helpers.get_plugins_json_file_path_from_dir_path(temp_plugin_dir)
    grafana_plugin_obj = helpers.read_plugin_details_from_plugin_json_file(plugin_json_file_path)  # When getting back an object from this method we know the object is validated - it has attributes: 'name' and 'version'
    
    plugin_id             = grafana_plugin_obj.id
    plugin_version        = grafana_plugin_obj.version
    grafana_plugins_dir   = app.config['GRAFANA_PLUGINS_DIR']
    plugin_zip_target_dir = join_path(grafana_plugins_dir, plugin_id, "versions", plugin_version)
    copied_zip_file_path  = helpers.copy_zip_file_to_plugins_dir(temp_uploaded_file_path, plugin_zip_target_dir)
    file_path             = copied_zip_file_path
    
    try:
        helpers.copy_file(plugin_json_file_path, join_path(plugin_zip_target_dir, "plugin.json"))
        logging.info(f'Success uploading and extracting file: {uploaded_file.filename}')
        logging.info(f'Cleaning uploaded and temp files..')
        helpers.delete_file(temp_uploaded_file_path)
        helpers.remove_directory_with_content(temp_plugin_dir)
    except Exception as e:
        logging.error(f'Error while uploading file: {str(e)}')
        helpers.delete_file(file_path)
        helpers.remove_directory_with_content(temp_plugin_dir)
        error_message = f'Error: {str(e)}\n'
        return error_message

    return redirect(url_for('index'))
