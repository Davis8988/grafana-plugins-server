from modules import runtime_config
from modules import helpers
import logging

def validate_uploaded_zip_file(zip_file_obj):
    zip_file_path = zip_file_obj.file_path
    logging.info(f'Validating uploaded zip file: {zip_file_path}')
    if not zip_file_obj or not helpers.allowed_file(zip_file_obj.filename):
        error_message = f'Error uploading: "{zip_file_obj.filename}" - Invalid file or file type not allowed. Only "*.zip" files are allowed'
        logging.error(error_message)
        flash(error_message)
        return False
    if not file_exists(zip_file_path):
        error_message = f'Missing or unreachable uploaded zip file: {zip_file_path} - cannot validate it'
        logging.error(error_message)
        flash(error_message)
        return False
    helpers.print_zip_file_containing_files(zip_file_path)
    helpers.get_plugins_json_file_path_from_zip_file(zip_file_path)
    return True
