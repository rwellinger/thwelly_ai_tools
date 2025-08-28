#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import time 
import hashlib

# 1️⃣ Lade .env
load_dotenv()

# 2️⃣ Konfiguriere Flask-App
app = Flask(__name__)

def ensure_images_dir() -> Path:
    """Erstellt den images-Ordner, wenn er nicht existiert."""
    images_path = Path(__file__).parent / "images"
    try:
        images_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Folder '{images_path}' created or exists already.", file=sys.stderr)
    except Exception as e:
        print(f"❌ Error on create folder: {e}", file=sys.stderr)
        raise
    return images_path

# 👉 Route zum Serven gespeicherter Bilder
@app.route('/images/<path:filename>')
def serve_image(filename):
    images_dir = ensure_images_dir()
    return send_from_directory(images_dir, filename)

@app.route('/generate', methods=['POST'])
def generate():
    raw_json = request.get_json(silent=True)

    # Überprüfen, ob 'prompt' und 'size' im JSON vorhanden sind
    if not raw_json or 'prompt' not in raw_json or 'size' not in raw_json:
        return jsonify({"error": "No 'prompt' or 'size' in JSON."}), 400
        
    prompt = raw_json['prompt']
    size = raw_json['size']  # Hole die Bildgröße aus dem Request-Body
    
    # Debug Ausgaben in den Server-Logs
    print(f"📝 Prompt: {prompt}", file=sys.stderr)
    print(f"📝 Size:   {size}", file=sys.stderr)
    
    # -------------------- OpenAI API Aufruf --------------------
    headers = {
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': os.getenv("OPENAI_MODEL"),
        'prompt': prompt,
        'size': size,
        'n': 1
    }
    
    try:
        resp = requests.post(os.path.join(os.getenv("OPENAI_URL"), "generations"), headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Network-Error: {e}"}), 500

    if resp.status_code != 200:
        print("DALL·E Response:", resp.text, file=sys.stderr)
        return jsonify({"error": resp.json()}), resp.status_code

    resp_json = resp.json()
    image_url = resp_json['data'][0]['url']
    
    # -------------------- Bild herunterladen --------------------
    try:
        img_resp = requests.get(image_url, stream=True, timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Download-Error: {e}"}), 500

    images_dir = ensure_images_dir()
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
    filename = f"{prompt_hash}_{int(time.time())}.png"    
    image_path = images_dir / filename

    try:
        with open(image_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"📁 Image stored here: {image_path}", file=sys.stderr)
    except Exception as e:
        return jsonify({"error": f"Error on persist image: {e}"}), 500

    # 👉 Lokale URL zurückgeben (z. B. http://localhost:5000/images/file.png)
    local_url = f"{request.host_url}images/{filename}"

    return jsonify({
        "url": local_url,
        "saved_path": str(image_path)
    })

# ---------------------------------------------------------------
# Server-Start
# ---------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv("OPENAI_PORT", 5000))
    print(f"🚀 Flask-Server läuft auf http://0.0.0.0:{port}", file=sys.stderr)
    app.run(host="0.0.0.0", port=port, debug=False)
