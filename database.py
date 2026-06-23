from extensions import db

def init_database(app):
    with app.app_context():
        db.create_all()
