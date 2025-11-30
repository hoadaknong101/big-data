import os
from flask import Flask, render_template
from flask_cors import CORS
from models import db
from routes import api_bp
from websocket import socketio, background_stats_emitter
from dotenv import load_dotenv
import threading

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dashboard_secret_key_change_in_production'
    
    # Database Config
    DB_USER = os.environ.get('POSTGRES_USER', 'postgres')
    DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')
    DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    DB_NAME = os.environ.get('POSTGRES_DB', 'bigdata_db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    socketio.init_app(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Routes
    @app.route('/')
    def index():
        """Trang chủ - Real-time Analytics"""
        return render_template('index.html')
    
    @app.route('/data-management')
    def data_management():
        """Trang quản lý dữ liệu và training"""
        return render_template('data_management.html')
    
    @app.route('/movies')
    def movies():
        """Trang quản lý phim"""
        return render_template('movies.html')
    
    @app.route('/users')
    def users():
        """Trang quản lý người dùng"""
        return render_template('users.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy'}, 200
    
    # Start background task for WebSocket stats emitter
    @socketio.on('connect')
    def on_connect():
        """Khi client connect, start background task nếu chưa chạy"""
        pass
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Start background stats emitter in a separate thread
    stats_thread = threading.Thread(
        target=background_stats_emitter,
        args=(app,),
        daemon=True
    )
    stats_thread.start()
    
    # Run app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
