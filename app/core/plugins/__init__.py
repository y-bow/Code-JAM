import json
import os
import importlib.util

from flask import Blueprint
from ...models import db, PluginState


class PluginManager:
    def __init__(self, app=None):
        self.app = app
        self.plugins = {}
        self._blueprints = []

    def init_app(self, app):
        self.app = app
        self._discover_plugins()
        self._load_active_plugins()
        return self

    def _discover_plugins(self):
        plugins_dir = os.path.join(self.app.root_path, '..', 'plugins')
        plugins_dir = os.path.normpath(plugins_dir)

        if not os.path.isdir(plugins_dir):
            return

        for slug in os.listdir(plugins_dir):
            plugin_dir = os.path.join(plugins_dir, slug)
            manifest_path = os.path.join(plugin_dir, 'plugin.json')

            if not os.path.isdir(plugin_dir) or not os.path.isfile(manifest_path):
                continue

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                manifest['slug'] = slug
                manifest['_dir'] = plugin_dir
                self.plugins[slug] = manifest
            except (json.JSONDecodeError, IOError):
                pass

    def _load_active_plugins(self):
        with self.app.app_context():
            active_slugs = set()
            try:
                records = PluginState.query.filter_by(is_active=True).all()
                active_slugs = {r.slug for r in records}
            except Exception:
                pass

        for slug, manifest in self.plugins.items():
            if slug in active_slugs:
                self._activate_plugin(slug, manifest)

    def _activate_plugin(self, slug, manifest):
        plugin_dir = manifest['_dir']
        entry_point = manifest.get('entry_point', 'plugin:Plugin')
        module_path = os.path.join(plugin_dir, '__init__.py')

        if not os.path.isfile(module_path):
            return

        try:
            spec = importlib.util.spec_from_file_location(f'plugins.{slug}', module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            class_name = entry_point.split(':')[1] if ':' in entry_point else 'Plugin'
            plugin_class = getattr(module, class_name, None)

            if plugin_class and hasattr(plugin_class, 'register_blueprints'):
                from .base import HivePlugin
                if issubclass(plugin_class, HivePlugin):
                    instance = plugin_class(self.app, manifest)
                    for bp in instance.register_blueprints():
                        self._blueprints.append(bp)
                        self.app.register_blueprint(bp)

                    tpl = instance.get_template_folder()
                    if tpl:
                        from flask import Flask
                        pass
        except Exception as e:
            self.app.logger.error(f'Failed to load plugin {slug}: {e}')

    def get_blueprints(self):
        return self._blueprints

    def get_installed_plugins(self):
        return list(self.plugins.values())

    def get_active_slugs(self):
        try:
            with self.app.app_context():
                records = PluginState.query.filter_by(is_active=True).all()
                return {r.slug for r in records}
        except Exception:
            return set()
