from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(150), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    occupation = db.Column(db.Integer, nullable=True)
    zip = db.Column(db.String(150), nullable=True)
    dataset_user_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'gender': self.gender,
            'age': self.age,
            'occupation': self.occupation,
            'zip': self.zip,
            'dataset_user_id': self.dataset_user_id
        }

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    genres = db.Column(db.String(255))
    poster_url = db.Column(db.String(500), nullable=True)
    overview = db.Column(db.Text, nullable=True)
    release_date = db.Column(db.String(20), nullable=True)
    rating_avg = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genres': self.genres,
            'poster_url': self.poster_url or 'https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg',
            'overview': self.overview or 'No overview available.',
            'release_date': self.release_date,
            'rating_avg': self.rating_avg
        }

class UserEvent(db.Model):
    __tablename__ = 'user_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_timestamp = db.Column(db.DateTime, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'event_type': self.event_type,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
