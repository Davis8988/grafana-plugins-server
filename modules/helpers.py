from classes import grafana_plugin as grafana_plugin_class
from distutils.version import StrictVersion
from modules import runtime_config
from flask import Response
import os
from time import sleep
from os.path import join as join_path
import zipfile
import logging
import shutil
import json

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

def prepare_grafana_plugins_dir(dir_path):
    if os.path.exists(dir_path):
        return
    print(f"Creating dir: {dir_path}")
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception as e:
        print(f'Error while attempting to create grafana plugins dir: {dir_path}')
        print(f'{str(e)}')
        raise Exception(f'Failed to create create grafana plugins dir: "{dir_path}" - {str(e)}')
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in runtime_config.app.config['ALLOWED_EXTENSIONS']




def flask_logger():
    """reads logging information"""
    with open(runtime_config.log_file_path) as f:
        while True:
            yield f.read()
            sleep(1)
    # Create empty logfile, old logging will be deleted
    open(runtime_config.log_file_path, 'w').close()

def stream():
    """returns logging information"""
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


def search_plugin_json_in_zip_file_namelist(file_list):
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
    

def print_zip_file_containing_files(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Check if plugin.json exists in the zip file
        file_list = zip_ref.namelist()
        logging.info(f'Listing files under uploaded zip: {zip_file}')
        for x in file_list:
            logging.info(f' - {x}')

def get_plugins_json_file_path_from_dir_path(dir_path):
    logging.info(f'Searching for "plugin.json" file under: {dir_path}')
    file_name = "plugin.json"
    for root, dirs, files in os.walk(dir_path):
        if file_name in files:
            return os.path.join(root, file_name)
    logging.warning(f'Failed to find "plugin.json" file under: {dir_path}')
    return None

def get_all_files_by_name_under_dir_path(file_name, dir_path):
    logging.info(f'Searching for all "{file_name}" files under: {dir_path}')
    found_files_arr = []
    for root, dirs, files in os.walk(dir_path):
        if file_name in files:
            found_files_arr.append(os.path.join(root, file_name))
    return found_files_arr

def get_plugins_json_file_path_from_zip_file(zip_file):
    plugin_json_file_path = None
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        # Check if plugin.json exists in the zip file
        file_list = zip_ref.namelist()

        # Search for plugin.json recursively
        plugin_json_file_path = search_plugin_json_in_zip_file_namelist(file_list)
    if not plugin_json_file_path:
        raise Exception(f'"plugin.json" not found in the uploaded zip file: {zip_file}')
    return plugin_json_file_path

def file_exists(file_path):
    return os.path.exists(file_path)

def dir_exists(dir_path):
    return os.path.exists(dir_path)

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
    
def copy_zip_file_to_plugins_dir(zip_file_path, plugin_zip_target_dir):
    create_dir(plugin_zip_target_dir)
    zip_file_name      = get_file_name_from_path(zip_file_path)
    dest_zip_file_path = join_path(plugin_zip_target_dir, zip_file_name)
    copy_file(zip_file_path, dest_zip_file_path)
    return dest_zip_file_path

def get_file_name_from_path(file_path):
    # if not file_exists(file_path):
        # logging.error(f'Missing or unreachable file path: {file_path} - cannot get its name')
        # raise Exception(f'Missing or unreachable file path: {file_path} - cannot get its name')
    return os.path.basename(file_path)


def extract_zip_to_dir(src_zip_file, dest_dir_to_extract_to):
    logging.info(f'Extracting zip file: {src_zip_file} to: {dest_dir_to_extract_to}')
    remove_directory_with_content(dest_dir_to_extract_to)
    try:
        with zipfile.ZipFile(src_zip_file, 'r') as zip_ref:
            zip_ref.extractall(dest_dir_to_extract_to)
    except Exception as e:
        logging.error(f'Error while extracting zip file: {src_zip_file} to: {dest_dir_to_extract_to}')
        raise Exception(f'Error while extracting zip file: {src_zip_file} to: {dest_dir_to_extract_to} - {str(e)}')
    return dest_dir_to_extract_to
    
def extract_file_from_zip_to_dir(src_zip_file, file_to_extract, dest_dir_to_extract_to):
    logging.info(f'Extracting {file_to_extract} from: {src_zip_file} to: {dest_dir_to_extract_to}')
    # extract_file_name = get_file_name_from_path(file_to_extract)
    create_dir(dest_dir_to_extract_to)
    # dest_file_path = join_path(dest_dir_to_extract_to, extract_file_name)
    dest_file_path = join_path(dest_dir_to_extract_to, file_to_extract)
    delete_file(dest_file_path)  # Remove old file if it already exists..
    with zipfile.ZipFile(src_zip_file, 'r') as zip_ref:
        zip_ref.extract(file_to_extract, path=dest_dir_to_extract_to)
    logging.info(f'Success extracting {file_to_extract} from: {src_zip_file} to: {dest_dir_to_extract_to}')
    return dest_file_path
    

def remove_directory_with_content(dir_path):
    if not dir_exists(dir_path):
        return
    logging.info(f'Removing directory with its content: {dir_path}')
    try:
        for root, dirs, files in os.walk(dir_path):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        shutil.rmtree(dir_path)
        if os.path.exists(dir_path):
            raise Exception(f'Even after removing the directory: "{dir_path}" it still exists')
    except Exception as e:
        logging.error(f'Error while removing the directory: {dir_path}')
        logging.error(f'{str(e)}')
        raise Exception(f'Error: Failed to remove the directory: {dir_path}')
    logging.info(f'Success removing the directory with its content: {dir_path}')

def read_json_file(json_file_path):
    logging.info(f'Reading json file: {json_file_path}')
    if not file_exists(json_file_path):
        logging.error(f'Missing or unreachable json file: {json_file_path} - cannot read it')
        raise Exception(f'Missing or unreachable json file: {json_file_path} - cannot read it')
    # Read JSON file
    json_data = None
    try:
        with open(json_file_path) as file:
            json_data = json.load(file)
    except Exception as e:
        logging.error(f'Error while attempting to read json file: {json_file_path}')
        logging.error(str(e))
        raise e
    return json_data
  
def read_plugin_details_from_plugin_json_file(plugin_json_file_path):
    logging.info(f'Reading plugin details from: {plugin_json_file_path}')
    json_data = read_json_file(plugin_json_file_path)
    if not json_data:
        err_msg = f"Read json data from file: {plugin_json_file_path} is of Null/empty value ''"
        logging.error(err_msg)
        raise Exception(err_msg)
    logging.info(json_data)
    logging.info("OK")
    logging.info("Parsing json data into a GrafanaPlugin class obj")
    
    grafana_plugin_obj = grafana_plugin_class.GrafanaPlugin(**json_data) # Create GrafanaPlugin instance
    grafana_plugin_class.validate_grafana_plugin_class_obj(grafana_plugin_obj)
    return grafana_plugin_obj

def list_first_level_dirs_under_path(dir_path):
    logging.info("Listing 1st level directories under: {dir_path} ")
    try:
        return [ name for name in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, name)) ]  # Get only dirs
    except Exception as e:
        logging.info(f'Failed to list 1st level directories under path: {dir_path} ')
        logging.error(f'Error while attempting to list 1st level directories under path: {str(e)}')
        raise e

def construct_plugins_summary_json_file_data():
    logging.info('Constructing all plugins summary json file content')
    # Construct the JSON structure
    plugins_summary_json_file_data = {
        "plugins": []
    }
    
    all_plugins_json_files_arr = get_all_files_by_name_under_dir_path('plugin.json', runtime_config.grafana_plugins_dir)
    if len(all_plugins_json_files_arr) == 0:
        logging.warning(f"No 'plugin.json' files found in 1st level content of all directories under: {runtime_config.grafana_plugins_dir}")
        logging.warning("Cannot calculate plugins summary json file since no plugin.json files were found")
        return plugins_summary_json_file_data
    grafana_plugins_obj_arr = []
    for grafana_plugin_json_file in all_plugins_json_files_arr:
        grafana_plugin_obj = read_plugin_details_from_plugin_json_file(grafana_plugin_json_file)  # Also validates it..
        grafana_plugins_obj_arr.append(grafana_plugin_obj)
    if len(grafana_plugins_obj_arr) == 0:
        err_msg = f"Failed to read any of 'plugin.json' files found({len(all_plugins_json_files_arr)}) under 1st level content of all directories under: {runtime_config.grafana_plugins_dir}"
        logging.error(err_msg)
        return plugins_summary_json_file_data

    parsed_plugins_map = {}
    for plugin_obj in grafana_plugins_obj_arr:
        if not parsed_plugins_map.get(plugin_obj.id, None):
            parsed_plugins_map[plugin_obj.id] = {
                'plugin_obj'         : plugin_obj,
                'plugin_versions_map': {}
            }
        plugin_versions_map = parsed_plugins_map[plugin_obj.id].get('plugin_versions_map')
        plugin_versions_map[plugin_obj.version] = plugin_obj.version
    
    for parsed_plugin_id, parsed_plugin_versions_map in parsed_plugins_map.items():
        plugin_obj = parsed_plugin_versions_map['plugin_obj']
        versions_arr = [version for version in plugin_versions_map.keys()]
        versions_arr.sort(key=StrictVersion, reverse=True)  # Need to use reverse here since the lowest value is first on normal sorting..
        versions_arr = [ {"version" : version } for version in versions_arr ]  # Convert format of each item to: { "version" : version }
        plugin_json_data = {
            "id": parsed_plugin_id,
            "type": plugin_obj.type,
            "versions" : versions_arr
        }
        plugins_summary_json_file_data["plugins"].append(plugin_json_data)
    return plugins_summary_json_file_data
    

def write_json_file(json_data, json_file_path):
    # Write JSON data to a file
    logging.info(f'Writing json data to: {json_file_path}')
    delete_file(json_file_path)
    try:
        with open(json_file_path, 'w') as file:
            json.dump(json_data, file, indent=4)
    except Exception as e:
        logging.error(f'Failed to write json data to file: {json_file_path}')
        raise Exception(f'Failed to write json data to file: {json_file_path} - {str(e)}')

def calculate_uploaded_plugins_summary_json_file():
    logging.info('Calculating uploaded plugins summary json file')
    plugins_summary_json_file_content = construct_plugins_summary_json_file_data()
    if not plugins_summary_json_file_content:
        err_msg = f"Failed to construct plugins summary json file content from all 'plugin.json' files found({len(all_plugins_json_files_arr)}) under 1st level content of all directories under: {runtime_config.grafana_plugins_dir}"
        logging.error(err_msg)
        raise Exception(err_msg)
    write_json_file(plugins_summary_json_file_content, runtime_config.grafana_plugins_summary_json_file)
    