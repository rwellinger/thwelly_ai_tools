from flask import Blueprint
from controllers.openai_controller import OpenAIController

openai_routes = Blueprint('openai', __name__)
controller = OpenAIController()


@openai_routes.route('/images/generations', methods=['POST'])
def generate_image():
    """Simulation of https://api.openai.com/v1/images/generations"""
    print("Generating image")
    return controller.generate_image()
