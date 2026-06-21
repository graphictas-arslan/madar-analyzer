from flask import Flask
from config import Config
from database import init_database
from extensions import db, migrate
from auth.routes import auth_bp

import models

app = Flask(__name__)

app.config.from_object(Config)
app.register_blueprint(auth_bp)


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

app.config["SECRET_KEY"] = "tas-super-secret-key"