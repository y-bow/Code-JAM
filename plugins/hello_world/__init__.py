from flask import Blueprint, render_template_string
from app.core.plugins.base import HivePlugin

hello_bp = Blueprint('hello_world', __name__, url_prefix='/hello', template_folder='templates')


@hello_bp.route('/')
def index():
    return render_template_string('''
        <h2>Hello from Hello World Plugin!</h2>
        <p>This page is served by a Hive plugin.</p>
    ''')


class HelloWorldPlugin(HivePlugin):
    def register_blueprints(self):
        return [hello_bp]

    def on_enable(self):
        self.app.logger.info('HelloWorld plugin enabled')

    def on_disable(self):
        self.app.logger.info('HelloWorld plugin disabled')
