from flask import Flask
from config import Config
from database import init_database
from extensions import db, migrate
from auth.routes import bot_bp
from dashboard.routes import dashboard_bp
import models

app = Flask(__name__)

app.config.from_object(Config)
app.config["SECRET_KEY"] = "tas-super-secret-key"

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(bot_bp)
app.register_blueprint(dashboard_bp)

init_database(app)


@app.route("/")
def home():
    return "Bale Analyzer is Running 🚀"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )