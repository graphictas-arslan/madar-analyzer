import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


BALE_TOKEN = os.environ.get("BALE_TOKEN")
