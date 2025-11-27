import os
from flask import Flask
from flask_login import LoginManager
from models import db, User
from routes import auth_bp, main_bp
from dotenv import load_dotenv

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key_here' # Change this in production
    
    if test_config:
        app.config.update(test_config)
    else:
        # Database Config
        DB_USER = os.environ.get('POSTGRES_USER', 'postgres')
        DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')
        DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
        DB_NAME = os.environ.get('POSTGRES_DB', 'bigdata_db')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)
