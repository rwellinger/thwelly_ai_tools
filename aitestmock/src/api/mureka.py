from flask import Blueprint
from controllers.mureka_controller import MurekaController

mureka_routes = Blueprint('mureka', __name__)
controller = MurekaController()


@mureka_routes.route('/song/generate', methods=['POST'])
def generate_song():
    return controller.generate_song()


@mureka_routes.route('/song/stem', methods=['POST'])
def generate_stem():
    return controller.generate_stem()


@mureka_routes.route('/song/query', methods=['GET'])
def query_song_status():
    return controller.query_song_status()


@mureka_routes.route('/account/billing', methods=['GET'])
def get_billing_info():
    return controller.get_billing_info()