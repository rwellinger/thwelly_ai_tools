from flask import Blueprint
from controllers.mureka_controller import MurekaController

mureka_routes = Blueprint('mureka', __name__)
controller = MurekaController()


@mureka_routes.route('/song/generate', methods=['POST'])
def generate_song():
    """Simulation of https://api.mureka.ai/v1/song/generate"""
    print("Generating song")
    return controller.generate_song()


@mureka_routes.route('/song/stem', methods=['POST'])
def generate_stem():
    """Simulation of https://api.mureka.ai/v1/song/stem"""
    print("Generating stem")
    return controller.generate_stem()


@mureka_routes.route('/song/query/<job_id>', methods=['GET'])
def query_song_status(job_id):
    """Simulation of https://api.mureka.ai/v1/song/query/<job_id>"""
    print("Querying song status for job {}".format(job_id))
    return controller.query_song_status(job_id)


@mureka_routes.route('/account/billing', methods=['GET'])
def get_billing_info():
    """Simulation of https://api.mureka.ai/v1/account/billing"""
    print("Getting billing info")
    return controller.get_billing_info()
