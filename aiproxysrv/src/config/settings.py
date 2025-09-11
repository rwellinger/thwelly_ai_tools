"""
Zentrale Konfiguration für alle Module
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# Celery Config
# --------------------------------------------------
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# --------------------------------------------------
# MUREKA Config
# --------------------------------------------------
MUREKA_GENERATE_ENDPOINT = os.getenv("MUREKA_GENERATE_ENDPOINT")
MUREKA_STEM_GENERATE_ENDPOINT = os.getenv("MUREKA_STEM_GENERATE_ENDPOINT")
MUREKA_STATUS_ENDPOINT = os.getenv("MUREKA_STATUS_ENDPOINT")
MUREKA_API_KEY = os.getenv("MUREKA_API_KEY")
MUREKA_BILLING_URL = os.getenv("MUREKA_BILLING_URL")
MUREKA_TIMEOUT = int(os.getenv("MUREKA_TIMEOUT", "30"))
MUREKA_POLL_INTERVAL = int(os.getenv("MUREKA_POLL_INTERVAL", "15"))
MUREKA_MAX_POLL_ATTEMPTS = int(os.getenv("MUREKA_MAX_POLL_ATTEMPTS", "240"))

# --------------------------------------------------
# OpenAI Config
# --------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = os.getenv("OPENAI_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# --------------------------------------------------
# Server Config
# --------------------------------------------------
OPENAI_PORT = int(os.getenv("OPENAI_PORT", "5050"))
OPENAI_HOST = os.getenv("OPENAI_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# --------------------------------------------------
# Image Storage Config
# --------------------------------------------------
IMAGES_DIR = os.getenv("IMAGES_DIR", "./images" if DEBUG else "/images")

# --------------------------------------------------
# Redis Config (falls verwendet)
# --------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --------------------------------------------------
# Database Config
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql://aiproxy:aiproxy123@10.0.1.120:5432/aiproxysrv"
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
