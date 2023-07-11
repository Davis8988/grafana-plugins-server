from modules import runtime_config
from modules import helpers
from modules import grafana_plugin_file
from flask import render_template, request, redirect, url_for, send_from_directory, Response, jsonify
from flask import flash
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
                            app=app,
                            helpers=helpers,
                            runtime_config=runtime_config)

@app.route('/plugins/download/<path:filename>', methods=['GET'])
def download_file_from_plugins(filename):
    logging.info(f'Accessed plugins/download/{filename} page')
    directory = app.config['GRAFANA_PLUGINS_DIR']
    logging.info(f"Returning plugin zip file: {filename} for download")
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/plugins/<path:plugin_id>/versions/<path:plugin_version>/download', methods=['GET'])
def download_plugin(plugin_id, plugin_version):
    logging.info(f'Accessed plugins/{plugin_id}/versions/{plugin_version}/download page')
    plugin_version_dir = join_path(app.config['GRAFANA_PLUGINS_DIR'], plugin_id, 'versions', plugin_version)
    if not helpers.dir_exists(plugin_version_dir):
        logging.error(f"Missing or unreachable plugin: '{plugin_id}' version dir: \"{plugin_version_dir}\" - cannot download this plugin")
        return jsonify({})
    logging.info(f"Searching for plugin: '{plugin_id}' .zip file under path: {plugin_version_dir}")
    first_level_files = [file_name for file_name in helpers.list_first_level_files_under_path(plugin_version_dir) if file_name.endswith(".zip")]
    if len(first_level_files) == 0:
        logging.error(f"Did not find any plugin: '{plugin_id}'  .zip files under version dir: \"{plugin_version_dir}\" - cannot download this plugin")
        return jsonify({})
    plugin_zip_file_name = first_level_files[0]
    logging.info(f"Returning plugin zip file: {plugin_zip_file_name} for download")
    return send_from_directory(plugin_version_dir, plugin_zip_file_name, as_attachment=True)

@app.route('/plugins/repo', methods = ['GET'])
def plugins_repo_page():
    logging.info('Accessed plugins/repo page')
    helpers.calculate_uploaded_plugins_summary_json_file()
    json_data = helpers.read_json_file(runtime_config.grafana_plugins_summary_json_file)
    json_pretty_data = helpers.get_pretty_json_data_str(json_data)
    logging.info(f"Returning json data")
    if json_pretty_data:
        logging.info(f'\n{json_pretty_data}')
    return jsonify(json_data)

@app.route('/plugins/repo/<path:plugin_id>', methods = ['GET'])
def plugins_repo_list_plugin_versions_page(plugin_id):
    logging.info(f'Accessed plugins/repo/{plugin_id} page')
    plugin_versions_json_file_content = helpers.construct_plugin_versions_json_file_data(plugin_id)
    if not plugin_versions_json_file_content:
        logging.error(f'plugin_versions_json_file_content is null')
        plugin_versions_json_file_content = {}
    logging.info(f"Returning json data")
    logging.info(f"\n{plugin_versions_json_file_content}")
    return jsonify(plugin_versions_json_file_content)


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

@app.route('/remove_file', methods=['POST'])
def remove_file():
    directory_name = runtime_config.repo_name
    file_name = request.form['file_name']
    file_path = join_path(app.config['GRAFANA_PLUGINS_REPO_DIR'], file_name)
    helpers.delete_file(file_path)
    logging.info(f'Removed file: {file_name} from directory: {directory_name}')
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if not grafana_plugin_file.validate_uploaded_zip_file(uploaded_file):
        return redirect(url_for('index'))

    # Save the uploaded file into a temp dir first..
    extract_file_name           = uploaded_file.filename
    file_name_without_extension = os.path.splitext(extract_file_name)[0]
    temp_uploaded_file_path     = helpers.save_file_in_dir(uploaded_file, temp_grafana_plugins_dir)
    temp_plugin_dir             = join_path(temp_grafana_plugins_dir, file_name_without_extension)
    
    # Validate uploaded zip file:
    if not grafana_plugin_file.validate_temp_save_zip_file(temp_uploaded_file_path):
        return
        
    # Print
    helpers.print_zip_file_containing_files(temp_uploaded_file_path)
    
    # Get plugin.json file from inside the zip file
    plugin_json_file_in_zip = helpers.get_plugins_json_file_path_from_zip_file(temp_uploaded_file_path)  # On error it will raise an exception
    
    # Save file 'plugin.json' into a temp dir
    plugin_json_file_path = helpers.extract_file_from_zip_to_dir(temp_uploaded_file_path, plugin_json_file_in_zip, temp_plugin_dir)
    
    # Read plugin details:
    grafana_plugin_obj = helpers.read_plugin_details_from_plugin_json_file(plugin_json_file_path)  # When getting back an object from this method we know the object is validated - it has attributes: 'name' and 'version'
    
    plugin_id             = grafana_plugin_obj.id
    plugin_version        = grafana_plugin_obj.version
    grafana_plugins_dir   = app.config['GRAFANA_PLUGINS_DIR']
    plugin_zip_target_dir = join_path(grafana_plugins_dir, plugin_id, "versions", plugin_version)
    helpers.remove_directory_with_content(plugin_zip_target_dir)  # Remove the old dir (if exists) containing the specific version's files
    copied_zip_file_path  = helpers.copy_zip_file_to_plugins_dir(temp_uploaded_file_path, plugin_zip_target_dir)
    file_path             = copied_zip_file_path
    
    try:
        helpers.copy_file(plugin_json_file_path, join_path(plugin_zip_target_dir, "plugin.json"))
        info_message = f"Success uploading and extracting file:  '{uploaded_file.filename}'"
        logging.info(info_message)
        flash(info_message, 'info')
        logging.info(f'Cleaning uploaded and temp files..')
        # Cleanup..
        helpers.delete_file(temp_uploaded_file_path)
        helpers.remove_directory_with_content(temp_plugin_dir)
    except Exception as e:
        logging.error(f'Error while uploading file: {str(e)}')
        helpers.delete_file(file_path)
        helpers.remove_directory_with_content(temp_plugin_dir)
        error_message = f'Error: {str(e)}\n'
        flash(error_message, 'error')

    return redirect(url_for('index'))
