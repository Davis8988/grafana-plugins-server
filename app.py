from modules import runtime_config
from flask import Flask
import os
import sys
from os.path import join as join_path
import logging
from modules import helpers


app = Flask(__name__)
runtime_config.app = app

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
runtime_config.script_directory = script_directory
server_port              = os.environ.get('SERVER_PORT',         3011)
server_host              = os.environ.get('SERVER_HOST',      "0.0.0.0")
log_file_path            = os.environ.get('LOG_FILE',            join_path(script_directory, "logs", "app.log"))
grafana_plugins_dir      = os.environ.get('GRAFANA_PLUGINS_DIR', join_path(script_directory, "grafana_plugins"))
temp_grafana_plugins_dir = join_path(os.environ.get('TEMP_GRAFANA_PLUGINS_DIR', helpers.get_persistent_temp_dir()), "grafana_plguins")

runtime_config.server_port              = server_port
runtime_config.server_host              = server_host
runtime_config.log_file_path            = log_file_path
runtime_config.grafana_plugins_dir      = grafana_plugins_dir
runtime_config.temp_grafana_plugins_dir = temp_grafana_plugins_dir


# Configure app settings
app.config['GRAFANA_PLUGINS_DIR'] = grafana_plugins_dir
app.config['ALLOWED_EXTENSIONS']  = {'zip'}

# Prepare env:
helpers.prepare_logging_dir(log_file_path)
helpers.prepare_grafana_plugins_dir(grafana_plugins_dir)

# Set up logging
log_level = os.environ.get('LOG_LEVEL', logging.INFO)
# create formatter
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
logging.basicConfig(
    level=log_level,
    format=' %(asctime)s :: %(levelname)-5s :: %(message)s',  # Updated logging format
    datefmt="%Y-%m-%d  %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file_path),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# Add all routes
from modules import routes

if __name__ == '__main__':
    logging.info(f"Starting grafana plugins server on address: {server_host}:{server_port}")
    try:
        app.run(debug=True, port=server_port, host=server_host) 
    except Exception as e:
        logging.info(f'An exception has occurred during execution of the plugins server')
        logging.error(f'{str(e)}')
        raise e
