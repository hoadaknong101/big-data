from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Movie
import requests
import os
import random

auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)

API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL', 'http://localhost:5000')

# --- Auth Routes ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        print(check_password_hash(user.password, password))
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check your username and password.')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            email=email, 
            username=username, 
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            dataset_user_id=random.randint(1, 6040) # Randomly assign a dataset user ID for demo
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('main.dashboard'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- Main Routes ---
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    recommendations = []
    error = None
    
    if current_user.dataset_user_id:
        try:
            # Call API Gateway
            response = requests.get(f"{API_GATEWAY_URL}/recommendations/{current_user.dataset_user_id}")
            if response.status_code == 200:
                recommendations = response.json()
            else:
                error = "Could not fetch recommendations."
        except Exception as e:
            error = f"Error connecting to API Gateway: {e}"
    
    return render_template('dashboard.html', recommendations=recommendations, error=error)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update logic here (simplified)
        current_user.username = request.form.get('username')
        # current_user.dataset_user_id = request.form.get('dataset_user_id')
        db.session.commit()
        flash('Profile updated!')
        
    return render_template('profile.html')

@main_bp.route('/watch/<int:movie_id>')
@login_required
def watch(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    # Track Event: User watched a movie
    print(current_user.dataset_user_id)
    if current_user.dataset_user_id:
        try:
            payload = {
                "user_id": current_user.dataset_user_id,
                "movie_id": movie_id,
                "event_type": "watch"
            }
            # Fire and forget (timeout short to not block UI)
            requests.post(f"{API_GATEWAY_URL}/event", json=payload, timeout=1)
        except Exception as e:
            print(f"⚠️ Failed to log watch event: {e}")

    return render_template('watch.html', movie=movie)

# --- API Routes ---

@main_bp.route('/api/movies')
def api_movies():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    genre = request.args.get('genre')
    
    query = Movie.query
    if genre:
        query = query.filter(Movie.genres.ilike(f'%{genre}%'))
        
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movies = [movie.to_dict() for movie in pagination.items]
    
    return {
        'movies': movies,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }

@main_bp.route('/api/movie/<int:movie_id>')
def api_movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return movie.to_dict()

@main_bp.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return {'results': []}
    
    movies = Movie.query.filter(Movie.title.ilike(f'%{query}%')).limit(10).all()
    return {'results': [movie.to_dict() for movie in movies]}

@main_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    # Mock or fetch from API Gateway
    # For now, return random movies
    movies = Movie.query.order_by(db.func.random()).limit(10).all()
    return {'results': [movie.to_dict() for movie in movies]}

@main_bp.route('/api/trending')
def api_trending():
    # Logic: Get 30 random movies
    movies = Movie.query.order_by(db.func.random()).limit(30).all()
    return {'results': [movie.to_dict() for movie in movies]}
