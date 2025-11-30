from flask_socketio import SocketIO, emit
from flask import request
from models import db, UserEvent, Movie
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import time

socketio = SocketIO(cors_allowed_origins="*")

# Background task để emit real-time statistics
def background_stats_emitter(app):
    """
    Background task chạy liên tục để emit statistics mỗi 2 giây
    """
    with app.app_context():
        while True:
            try:
                # Lấy statistics từ database
                stats = get_realtime_stats()
                
                # Emit tới tất cả connected clients
                socketio.emit('stats_update', stats, namespace='/')
                
                # Sleep 2 giây
                socketio.sleep(2)
            except Exception as e:
                print(f"Error in background_stats_emitter: {e}")
                socketio.sleep(5)

def get_realtime_stats():
    """
    Lấy real-time statistics từ database
    """
    try:
        # 1. Event type distribution (pie chart data)
        event_distribution = db.session.query(
            UserEvent.event_type,
            func.count(UserEvent.id).label('count')
        ).group_by(UserEvent.event_type).all()
        
        event_dist_data = {
            'labels': [e[0] for e in event_distribution],
            'data': [e[1] for e in event_distribution]
        }
        
        # 2. Top 10 movies (bar chart data)
        top_movies = db.session.query(
            Movie.title,
            func.count(UserEvent.id).label('view_count')
        ).join(
            UserEvent, Movie.id == UserEvent.movie_id
        ).group_by(
            Movie.id, Movie.title
        ).order_by(
            desc('view_count')
        ).limit(10).all()
        
        # Reverse order for horizontal bar chart (highest at top)
        top_movies = list(reversed(top_movies))
        
        top_movies_data = {
            'labels': [m[0][:30] + '...' if len(m[0]) > 30 else m[0] for m in top_movies],
            'data': [m[1] for m in top_movies]
        }
        
        # If no data, provide sample data
        if not top_movies:
            top_movies_data = {
                'labels': ['Chưa có dữ liệu'],
                'data': [0]
            }
        
        # 3. Views over time (line chart data - last 24 hours)
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Group by hour
        hourly_views = db.session.query(
            func.date_trunc('hour', UserEvent.event_timestamp).label('hour'),
            func.count(UserEvent.id).label('count')
        ).filter(
            UserEvent.event_timestamp >= last_24h
        ).group_by(
            'hour'
        ).order_by(
            'hour'
        ).all()
        
        views_over_time_data = {
            'labels': [h[0].strftime('%H:%M') if h[0] else '' for h in hourly_views],
            'data': [h[1] for h in hourly_views]
        }
        
        # 4. Total statistics
        total_events = db.session.query(func.count(UserEvent.id)).scalar() or 0
        total_users = db.session.query(func.count(func.distinct(UserEvent.user_id))).scalar() or 0
        total_movies_watched = db.session.query(func.count(func.distinct(UserEvent.movie_id))).scalar() or 0
        
        # 5. Recent events (last 5)
        recent_events = db.session.query(
            UserEvent.user_id,
            Movie.title,
            UserEvent.event_type,
            UserEvent.event_timestamp
        ).join(
            Movie, Movie.id == UserEvent.movie_id
        ).order_by(
            desc(UserEvent.event_timestamp)
        ).limit(5).all()
        
        recent_events_data = [
            {
                'user_id': e[0],
                'movie_title': e[1],
                'event_type': e[2],
                'timestamp': e[3].strftime('%Y-%m-%d %H:%M:%S') if e[3] else ''
            }
            for e in recent_events
        ]
        
        return {
            'event_distribution': event_dist_data,
            'top_movies': top_movies_data,
            'views_over_time': views_over_time_data,
            'totals': {
                'events': total_events,
                'users': total_users,
                'movies': total_movies_watched
            },
            'recent_events': recent_events_data,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error getting realtime stats: {e}")
        return {
            'event_distribution': {'labels': [], 'data': []},
            'top_movies': {'labels': [], 'data': []},
            'views_over_time': {'labels': [], 'data': []},
            'totals': {'events': 0, 'users': 0, 'movies': 0},
            'recent_events': [],
            'timestamp': datetime.utcnow().isoformat()
        }

@socketio.on('connect')
def handle_connect():
    """
    Handler khi client kết nối
    """
    print(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handler khi client ngắt kết nối
    """
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_stats')
def handle_stats_request():
    """
    Handler khi client request statistics ngay lập tức
    """
    stats = get_realtime_stats()
    emit('stats_update', stats)
