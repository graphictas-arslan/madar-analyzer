from flask import Flask
from config import Config
from database import init_database
from extensions import db, migrate
from bot.routes import bot_bp
from dashboard.routes import dashboard_bp
from users.routes import users_bp
from dotenv import load_dotenv
import os
import models

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "fallback-super-secret-key")

app.register_blueprint(users_bp)
app.register_blueprint(bot_bp)
app.register_blueprint(dashboard_bp)

@app.route('/')
def index():
    return "Bale Analyzer is Running 🚀"

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)

# Initialize database tables
init_database(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
