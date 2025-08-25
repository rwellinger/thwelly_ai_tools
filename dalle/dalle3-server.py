#!/usr/bin/env python3
import os
import sys
import json
import requests
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import time  # Füge das time-Modul hier hinzu

# 1️⃣ Lade .env
load_dotenv()

# 2️⃣ Konfiguriere Flask‑App
app = Flask(__name__)

def ensure_images_dir() -> Path:
    """Erstellt den images-Ordner, wenn er nicht existiert."""
    images_path = Path(__file__).parent / "images"
    try:
        images_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Ordner '{images_path}' erstellt oder existiert bereits.", file=sys.stderr)
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Ordners: {e}", file=sys.stderr)
        raise
    return images_path

@app.route('/generate', methods=['POST'])
def generate():
    raw_json = request.get_json(silent=True)
    if not raw_json or 'prompt' not in raw_json:
        return jsonify({"error": "Kein 'prompt' im JSON."}), 400

    prompt = raw_json['prompt']
    print(f"📝 Prompt: {prompt}", file=sys.stderr)

    # -------------------- OpenAI Aufruf --------------------
    headers = {
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': os.getenv("OPENAI_MODEL"),  # Modell aus der .env
        'prompt': prompt,
        'size': '1024x1024',
        'n': 1
    }

    try:
        resp = requests.post(os.getenv("OPENAI_URL"), headers=headers, json=payload, timeout=30)
    except Exception as e:
        return jsonify({"error": f"Netzwerk-Fehler: {e}"}), 500

    if resp.status_code != 200:
        return jsonify({"error": resp.json()}), resp.status_code

    resp_json = resp.json()
    image_url = resp_json['data'][0]['url']

    # -------------------- Bild herunterladen --------------------
    try:
        img_resp = requests.get(image_url, stream=True, timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Download‑Fehler: {e}"}), 500

    images_dir = ensure_images_dir()
    safe_prompt = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt)[:50]
    filename = f"{safe_prompt}_{int(time.time())}.png"  # Nutzen das time-Modul hier
    image_path = images_dir / filename

    try:
        with open(image_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"📁 Bild gespeichert unter: {image_path}", file=sys.stderr)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Schreiben des Bildes: {e}"}), 500

    return jsonify({
        "url": image_url,
        "saved_path": str(image_path)
    })

# ---------------------------------------------------------------
# Server‑Start
# ---------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv("OPENAI_PORT", 5000))  # PORT aus der .env
    print(f"🚀 Flask-Server läuft auf http://0.0.0.0:{port}", file=sys.stderr)
    app.run(host="0.0.0.0", port=port, debug=False)