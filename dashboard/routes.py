from flask import Blueprint, jsonify, request
from models import db, Movie, User, UserEvent
from werkzeug.security import generate_password_hash
from sqlalchemy import func, desc, or_
import os
import sys
import threading

# Add parent directory to path to import model_training
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from model_training.train import train_and_ingest

api_bp = Blueprint('api', __name__)

# ==================== Statistics Endpoints ====================

@api_bp.route('/api/stats/realtime', methods=['GET'])
def get_realtime_stats():
    """
    Lấy statistics real-time (không qua WebSocket)
    """
    from websocket import get_realtime_stats as get_stats
    stats = get_stats()
    return jsonify(stats), 200

@api_bp.route('/api/stats/trending', methods=['GET'])
def get_trending():
    """
    Lấy top trending movies
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        trending = db.session.query(
            Movie.id,
            Movie.title,
            Movie.poster_url,
            Movie.genres,
            func.count(UserEvent.id).label('view_count')
        ).join(
            UserEvent, Movie.id == UserEvent.movie_id
        ).group_by(
            Movie.id, Movie.title, Movie.poster_url, Movie.genres
        ).order_by(
            desc('view_count')
        ).limit(limit).all()
        
        result = [
            {
                'id': t[0],
                'title': t[1],
                'poster_url': t[2] or 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
                'genres': t[3],
                'view_count': t[4]
            }
            for t in trending
        ]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== Model Training Endpoint ====================

# Global variable để track training status
training_status = {
    'is_training': False,
    'progress': 0,
    'message': '',
    'error': None
}

def run_training():
    """
    Chạy model training trong background thread (local execution)
    """
    global training_status
    
    try:
        training_status['is_training'] = True
        training_status['progress'] = 10
        training_status['message'] = 'Đang khởi động training...'
        
        training_status['progress'] = 20
        training_status['message'] = 'Đang kết nối database và Milvus...'
        
        # Gọi trực tiếp hàm train_and_ingest từ model_training
        training_status['progress'] = 30
        training_status['message'] = 'Đang tải dữ liệu...'
        
        # Execute training
        is_success = train_and_ingest()

        if not is_success:
            training_status['progress'] = 0
            training_status['message'] = 'Training lỗi'
            training_status['error'] = 'Training lỗi'
            
            return jsonify({
                'error': 'Training lỗi'
            }), 500
        
        training_status['progress'] = 100
        training_status['message'] = 'Training hoàn tất thành công!'
        training_status['error'] = None
            
    except Exception as e:
        training_status['progress'] = 0
        training_status['message'] = 'Training lỗi'
        training_status['error'] = str(e)
        print(f"Training error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        training_status['is_training'] = False


@api_bp.route('/api/train-model', methods=['POST'])
def train_model():
    """
    Trigger model training
    """
    global training_status
    
    if training_status['is_training']:
        return jsonify({
            'error': 'Training đang chạy, vui lòng đợi'
        }), 400
    
    # Reset status
    training_status = {
        'is_training': True,
        'progress': 0,
        'message': 'Đang khởi tạo...',
        'error': None
    }
    
    # Start training in background thread
    thread = threading.Thread(target=run_training)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Model training đã được khởi động'
    }), 200

@api_bp.route('/api/train-status', methods=['GET'])
def get_train_status():
    """
    Lấy training status
    """
    return jsonify(training_status), 200

# ==================== Movie CRUD Endpoints ====================

@api_bp.route('/api/movies', methods=['GET'])
def get_movies():
    """
    Lấy danh sách movies với pagination và search
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        query = Movie.query
        
        if search:
            query = query.filter(
                or_(
                    Movie.title.ilike(f'%{search}%'),
                    Movie.genres.ilike(f'%{search}%')
                )
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'movies': [movie.to_dict() for movie in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    """
    Lấy thông tin chi tiết 1 movie
    """
    try:
        movie = Movie.query.get_or_404(movie_id)
        return jsonify(movie.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@api_bp.route('/api/movies', methods=['POST'])
def create_movie():
    """
    Tạo movie mới
    """
    try:
        data = request.json
        
        # Find next available ID (since movies.id is INTEGER PRIMARY KEY, not SERIAL)
        max_id = db.session.query(func.max(Movie.id)).scalar() or 0
        next_id = max_id + 1
        
        movie = Movie(
            id=next_id,  # Manually assign ID
            title=data.get('title'),
            genres=data.get('genres'),
            poster_url=data.get('poster_url'),
            overview=data.get('overview'),
            release_date=data.get('release_date'),
            rating_avg=data.get('rating_avg', 0.0)
        )
        
        db.session.add(movie)
        db.session.commit()
        
        return jsonify({
            'message': 'Movie created successfully',
            'movie': movie.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating movie: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/movies/<int:movie_id>', methods=['PUT'])
def update_movie(movie_id):
    """
    Cập nhật movie
    """
    try:
        movie = Movie.query.get_or_404(movie_id)
        data = request.json
        
        movie.title = data.get('title', movie.title)
        movie.genres = data.get('genres', movie.genres)
        movie.poster_url = data.get('poster_url', movie.poster_url)
        movie.overview = data.get('overview', movie.overview)
        movie.release_date = data.get('release_date', movie.release_date)
        movie.rating_avg = data.get('rating_avg', movie.rating_avg)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Movie updated successfully',
            'movie': movie.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """
    Xóa movie
    """
    try:
        movie = Movie.query.get_or_404(movie_id)
        db.session.delete(movie)
        db.session.commit()
        
        return jsonify({
            'message': 'Movie deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== User CRUD Endpoints ====================

@api_bp.route('/api/users', methods=['GET'])
def get_users():
    """
    Lấy danh sách users với pagination và search
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        query = User.query
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Lấy thông tin chi tiết 1 user
    """
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@api_bp.route('/api/users', methods=['POST'])
def create_user():
    """
    Tạo user mới
    """
    try:
        data = request.json
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            or_(
                User.username == data.get('username'),
                User.email == data.get('email')
            )
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Username or email already exists'}), 400
        
        # Find next available ID (since users.id is INTEGER PRIMARY KEY, not SERIAL)
        max_id = db.session.query(func.max(User.id)).scalar() or 0
        next_id = max_id + 1
        
        user = User(
            id=next_id,  # Manually assign ID
            username=data.get('username'),
            email=data.get('email'),
            password=generate_password_hash(data.get('password', '123'), method='pbkdf2:sha256'),
            gender=data.get('gender'),
            age=data.get('age'),
            occupation=data.get('occupation'),
            zip=data.get('zip'),
            dataset_user_id=data.get('dataset_user_id')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Cập nhật user
    """
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.gender = data.get('gender', user.gender)
        user.age = data.get('age', user.age)
        user.occupation = data.get('occupation', user.occupation)
        user.zip = data.get('zip', user.zip)
        user.dataset_user_id = data.get('dataset_user_id', user.dataset_user_id)
        
        # Only update password if provided
        if data.get('password'):
            user.password = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Xóa user
    """
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
