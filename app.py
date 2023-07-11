from modules import runtime_config
from flask import Flask
from waitress import serve
from flask_bootstrap import Bootstrap
import os
import sys
from os.path import join as join_path
import logging
from logging.handlers import RotatingFileHandler
from modules import helpers


app = Flask(__name__)
runtime_config.app = app

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
runtime_config.script_directory = script_directory
flask_secret_key         = os.environ.get('FLASK_SECRET_KEY', "super-secret-key")
server_port              = os.environ.get('THREADS_COUNT',       100)  # Default 100 threads for waitress to function..
server_port              = os.environ.get('SERVER_PORT',         3011)
server_host              = os.environ.get('SERVER_HOST',      "0.0.0.0")
log_file_path            = os.environ.get('LOG_FILE',            join_path(script_directory, "logs", "app.log"))
grafana_plugins_dir      = os.environ.get('GRAFANA_PLUGINS_DIR', join_path(script_directory, "grafana_plugins"))
grafana_plugins_repo_dir = os.environ.get('GRAFANA_PLUGINS_REPO_DIR', join_path(grafana_plugins_dir, "repo"))
grafana_plugins_summary_json_file = os.environ.get('GRAFANA_PLUGINS_SUMMARY_JSON_FILE', join_path(grafana_plugins_dir, "plugins_summary.json"))
temp_grafana_plugins_dir = join_path(os.environ.get('TEMP_GRAFANA_PLUGINS_DIR', helpers.get_persistent_temp_dir()), "grafana_plguins")

app.secret_key = flask_secret_key

# Bootstrap
bootstrap = Bootstrap(app)

# Configure runtime vars
runtime_config.bootstrap                = bootstrap
runtime_config.secret_key               = flask_secret_key
runtime_config.server_port              = server_port
runtime_config.server_host              = server_host
runtime_config.log_file_path            = log_file_path
runtime_config.grafana_plugins_dir      = grafana_plugins_dir
runtime_config.grafana_plugins_repo_dir = grafana_plugins_repo_dir
runtime_config.grafana_plugins_summary_json_file = grafana_plugins_summary_json_file
runtime_config.temp_grafana_plugins_dir = temp_grafana_plugins_dir




# Configure app settings
app.config['GRAFANA_PLUGINS_DIR']      = grafana_plugins_dir
app.config['GRAFANA_PLUGINS_REPO_DIR'] = grafana_plugins_repo_dir
app.config['ALLOWED_EXTENSIONS']       = {'zip'}

# Prepare env:
helpers.prepare_logging_dir(log_file_path)
helpers.prepare_grafana_plugins_dir(grafana_plugins_dir)

# Set up logging
log_level = os.environ.get('LOG_LEVEL', logging.INFO)
# create formatter
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
# add a rotating handler
rotate_log_file_handler = RotatingFileHandler(log_file_path, maxBytes=40, backupCount=1)  # 1 kilobyte
logging.basicConfig(
    level=log_level,
    format=' %(asctime)s :: %(levelname)-5s :: %(message)s',  # Updated logging format
    datefmt="%Y-%m-%d  %H:%M:%S",
    handlers=[
        # logging.FileHandler(log_file_path),  # Log to file
        logging.StreamHandler(),  # Log to console
        rotate_log_file_handler  # Log File Rotate
    ]
)

# Add all routes
from modules import routes

def prepare_runtime_env():
    logging.info("Preparing runtime environment")
    helpers.create_dir(grafana_plugins_repo_dir)
    helpers.create_dir(temp_grafana_plugins_dir)
    logging.info("Success - Finished preparing runtime environment")

if __name__ == '__main__':
    while True:
        logging.info(f"Starting grafana plugins server on address: {server_host}:{server_port}")
        try:
            prepare_runtime_env()
            serve(app, port=server_port, host=server_host)
        except Exception as e:
            logging.info(f'An exception has occurred during execution of the plugins server')
            logging.error(f'{str(e)}')
            raise e
