from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users' # Separate table for web users to avoid conflict with dataset users
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(150), nullable=False)
    age = db.Column(db.String(150), nullable=False)
    occupation = db.Column(db.String(150), nullable=False)
    zip = db.Column(db.String(150), nullable=False)
    dataset_user_id = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    genres = db.Column(db.String(255))
    # Additional fields for UI (can be nullable if data not available yet)
    poster_url = db.Column(db.String(500), nullable=True)
    overview = db.Column(db.Text, nullable=True)
    release_date = db.Column(db.String(20), nullable=True)
    rating_avg = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genres': self.genres,
            'poster_url': self.poster_url or f"https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
            'overview': self.overview or "No overview available.",
            'release_date': self.release_date,
            'rating_avg': self.rating_avg
        }

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.Integer, primary_key=True) # Changed to Integer for SQLite compatibility if needed, or Serial in PG
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    rating = db.Column(db.Integer)
    timestamp = db.Column(db.Integer)
