

class GrafanaPlugin:
    def __init__(self, **kwargs):
        self.name         = kwargs.get('name', None)
        self.type         = kwargs.get('type', None)
        self.id           = kwargs.get('id', None)
        self.description  = kwargs.get('description', None)
        self.version      = kwargs.get('version', None)
        # self.dependencies = kwargs.get('dependencies', None)
