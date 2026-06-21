from flask import Flask
from config import Config
from database import init_database
from extensions import db, migrate

import models

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

init_database(app)


@app.route("/")
def home():
    return "Bale Analyzer is Running 🚀"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )