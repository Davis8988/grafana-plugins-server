from modules import runtime_config
from modules import helpers
import logging

def validate_uploaded_zip_file(zip_file_obj):
    zip_file_path = zip_file_obj.file_path
    logging.info(f'Validating uploaded zip file: {zip_file_path}')
    if not uploaded_file or not helpers.allowed_file(uploaded_file.filename):
        error_message = f'Error uploading: "{uploaded_file.filename}" - Invalid file or file type not allowed. Only "*.zip" files are allowed'
        logging.error(error_message)
        flash(error_message)
        return False
    if not file_exists(zip_file_path):
        error_message = f'Missing or unreachable uploaded zip file: {zip_file_path} - cannot validate it'
        logging.error(error_message)
        flash(error_message)
        return False
    print_zip_file_containing_files(zip_file_path)
    get_plugins_json_file_path_from_zip_file(zip_file_path)

def upload():
    uploaded_file = request.files['file']
    

    # Save the uploaded file into a temp dir first..
    extract_file_name           = uploaded_file.filename
    file_name_without_extension = os.path.splitext(extract_file_name)[0]
    temp_uploaded_file_path     = helpers.save_file_in_dir(uploaded_file, temp_grafana_plugins_dir)
    temp_plugin_dir             = join_path(temp_grafana_plugins_dir, file_name_without_extension)
    
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
