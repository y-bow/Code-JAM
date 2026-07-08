class HivePlugin:
    def __init__(self, app, manifest):
        self.app = app
        self.manifest = manifest

    def register_blueprints(self):
        return []

    def get_template_folder(self):
        return None

    def on_enable(self):
        pass

    def on_disable(self):
        pass
