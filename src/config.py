import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
API_KEY = os.getenv("API_KEY", "")