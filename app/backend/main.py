import os
from pathlib import Path
from dotenv import load_dotenv

from app import create_app

# WEBSITE_HOSTNAME is always set by App Service, RUNNING_IN_PRODUCTION is set in main.bicep
RUNNING_ON_AZURE = os.getenv("WEBSITE_HOSTNAME") is not None or os.getenv("RUNNING_IN_PRODUCTION") is not None

if not RUNNING_ON_AZURE:
    # Load .env file from backend directory
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(f"Warning: No .env file found at {env_path}")

app = create_app()