from modules import runtime_config
from flask import Response
import os
from time import sleep
from os.path import join as join_path
import zipfile
import logging
import shutil

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