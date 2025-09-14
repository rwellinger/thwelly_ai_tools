from flask import Blueprint
from controllers.openai_controller import OpenAIController

openai_routes = Blueprint('openai', __name__)
controller = OpenAIController()


@openai_routes.route('/images/generations', methods=['POST'])
def generate_image():
    print("Generating image")
    return controller.generate_image()
