"""
DALL-E Image Generation Routes
"""
import os
import sys
import requests
import time
import hashlib
from pathlib import Path
from flask import Blueprint, request, jsonify, send_from_directory
from config.settings import OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL

api_image_v1 = Blueprint("api_image_v1", __name__, url_prefix="/api/v1/image")


@api_image_v1.route('/<path:filename>')
def serve_image(filename):
    """Serviert gespeicherte Bilder"""
    return send_from_directory("/images", filename)


@api_image_v1.route('/generate', methods=['POST'])
def generate():
    """Generiert ein Bild mit DALL-E"""
    raw_json = request.get_json(silent=True)

    if not raw_json or 'prompt' not in raw_json or 'size' not in raw_json:
        return jsonify({"error": "No 'prompt' or 'size' in JSON."}), 400

    prompt = raw_json['prompt']
    size = raw_json['size']

    print(f"Prompt: {prompt}", file=sys.stderr)
    print(f"Size:   {size}", file=sys.stderr)

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': OPENAI_MODEL,
        'prompt': prompt,
        'size': size,
        'n': 1
    }

    try:
        resp = requests.post(
            os.path.join(OPENAI_URL, "generations"),
            headers=headers,
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Network-Error: {e}"}), 500

    if resp.status_code != 200:
        print("DALL·E Response:", resp.text, file=sys.stderr)
        return jsonify({"error": resp.json()}), resp.status_code

    resp_json = resp.json()
    image_url = resp_json['data'][0]['url']

    try:
        img_resp = requests.get(image_url, stream=True, timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Download-Error: {e}"}), 500

    images_dir = Path("/images")
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
    filename = f"{prompt_hash}_{int(time.time())}.png"
    image_path = images_dir / filename

    try:
        with open(image_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Image stored here: {image_path}", file=sys.stderr)
    except Exception as e:
        return jsonify({"error": f"Error on persist image: {e}"}), 500

    local_url = f"{request.host_url}image/{filename}"
    return jsonify({
        "url": local_url,
        "saved_path": str(image_path)
    })
