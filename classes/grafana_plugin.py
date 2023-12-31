import logging

class GrafanaPlugin:
    def __init__(self, **kwargs):
        self.name         = kwargs.get('name', None)
        self.type         = kwargs.get('type', None)
        self.id           = kwargs.get('id', None)
        self.description  = None
        self.version      = None
        info_obj = kwargs.get('info', None)
        if info_obj:
            self.description  = info_obj.get('description', None)
            self.version      = info_obj.get('version', None)
        # self.dependencies = kwargs.get('dependencies', None)


def validate_grafana_plugin_class_obj(grafana_plugin):
    logging.info("Validating grafana plugin class obj")
    required_attributes = ['name', 'type', 'id', 'description', 'version']
    for attr_name in required_attributes:
        attr_value = getattr(grafana_plugin, attr_name)
        if attr_value is None or not attr_value.strip():
            err_msg = f"Grafana plugin class obj is missing or has an empty value attribute: '{attr_name}'"
            logging.error(err_msg)
            return False
    return True