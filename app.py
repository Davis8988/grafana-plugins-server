from modules import global_config
from flask import Flask
import os
import sys
from os.path import join as join_path
import logging
from modules import helpers


app = Flask(__name__)
global_config.app = app

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
global_config.script_directory = script_directory
log_file_path            = os.environ.get('LOG_FILE',            join_path(script_directory, "logs", "app.log"))
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

# Add all routes
from modules import routes

if __name__ == '__main__':
    app.run(debug=True, port=3011) 
