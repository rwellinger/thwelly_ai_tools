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

# Adaptive Polling Intervals
MUREKA_POLL_INTERVAL_SHORT = int(os.getenv("MUREKA_POLL_INTERVAL_SHORT", "5"))
MUREKA_POLL_INTERVAL_MEDIUM = int(os.getenv("MUREKA_POLL_INTERVAL_MEDIUM", "15"))
MUREKA_POLL_INTERVAL_LONG = int(os.getenv("MUREKA_POLL_INTERVAL_LONG", "30"))

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
# Control if physical files should be deleted (defaults to true if not set)
# Only set to false in special cases where you want to keep files but delete DB records
DELETE_PHYSICAL_FILES = os.getenv("DELETE_PHYSICAL_FILES", "true").lower() == "true"

# --------------------------------------------------
# Redis Config (falls verwendet)
# --------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --------------------------------------------------
# Database Config
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL",
    "postgresql://aiproxy:aiproxy123@localhost:5432/aiproxysrv" if DEBUG else
    "postgresql://aiproxy:aiproxy123@postgres:5432/aiproxysrv"
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
