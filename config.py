import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:cDFAcUaUfElEhekNHEnlyFupaegkKqPe@postgres.railway.internal:5432/railway")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BALE_TOKEN = os.getenv("BALE_TOKEN")
