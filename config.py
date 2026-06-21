import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-this-secret"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///bot.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


BALE_TOKEN = os.getenv("BALE_TOKEN")
