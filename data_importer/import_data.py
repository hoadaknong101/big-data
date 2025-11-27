import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

# Lấy thông tin DB từ biến môi trường
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('POSTGRES_HOST')
DB_NAME = os.environ.get('POSTGRES_DB')
DB_PORT = 5432

DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

def wait_for_db():
    """Chờ cho đến khi Postgres sẵn sàng."""
    print("Đang chờ Postgres sẵn sàng...")
    retries = 10
    while retries > 0:
        try:
            engine = create_engine(DB_URL)
            engine.connect()
            print("✅ Postgres đã sẵn sàng!")
            return engine
        except Exception as e:
            print(f"Lỗi kết nối: {e}. Thử lại sau 5s...")
            retries -= 1
            time.sleep(5)
    print("❌ Không thể kết nối tới Postgres.")
    exit(1)

def create_tables(engine):
    """Tạo các bảng nếu chưa tồn tại."""
    print("Đang kiểm tra và tạo bảng...")
    with engine.connect() as conn:
        # Bảng users
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                gender VARCHAR(10),
                age INTEGER,
                occupation INTEGER,
                zip VARCHAR(20),
                email VARCHAR(150),
                password VARCHAR(150),
                username VARCHAR(150) UNIQUE,
                dataset_user_id INTEGER
            );
        """))
        
        # Bảng movies
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY,
                title VARCHAR(255),
                genres VARCHAR(255),
                poster_url VARCHAR(500),
                overview TEXT,
                release_date VARCHAR(20),
                rating_avg FLOAT
            );
        """))
        
        # Bảng ratings
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                movie_id INTEGER,
                rating INTEGER,
                timestamp INTEGER
            );
        """))
        conn.commit()
    print("✅ Tạo bảng hoàn tất.")

def load_data(engine):
    """Tải dữ liệu từ file .dat vào Postgres."""
    print("Bắt đầu tải dữ liệu MovieLens...")
    
    try:
        # Tải Users
        print("Đang tải users.dat...")
        # Map columns: user_id -> id (PK)
        u_cols = ['id', 'gender', 'age', 'occupation', 'zip']
        users = pd.read_csv('data/users.dat', sep='::', names=u_cols, engine='python', encoding='latin-1')
        
        # Thêm email và password
        print("Đang tạo email và password ngẫu nhiên...")
        users['email'] = users['id'].apply(lambda x: f"user{x}@example.com")
        users['username'] = users['id'].apply(lambda x: f"user{x}")
        users['dataset_user_id'] = users['id']
        
        # Hash password "123"
        default_password_hash = generate_password_hash("123", method='pbkdf2:sha256')
        users['password'] = default_password_hash
        
        # append để giữ lại schema đã tạo (bao gồm email, password)
        users.to_sql('users', engine, if_exists='append', index=False)
        print(f"Tải thành công {len(users)} users.")

        # Tải Movies
        print("Đang tải movies.dat...")
        # Map columns: movie_id -> id (PK)
        m_cols = ['id', 'title', 'genres']
        movies = pd.read_csv('data/movies.dat', sep='::', names=m_cols, engine='python', encoding='latin-1')
        
        # Tải Poster URLs từ movies.csv
        print("Đang tải poster URLs từ movies.csv...")
        try:
            # Đọc movies.csv, chỉ lấy cột movie_id và poster_url
            poster_df = pd.read_csv('data/movies.csv', usecols=['movie_id', 'poster_url'])
            
            # Merge với bảng movies chính (Left Join để giữ lại tất cả phim từ movies.dat)
            movies = pd.merge(movies, poster_df, left_on='id', right_on='movie_id', how='left')
            
            # Xử lý các giá trị thiếu (NaN) nếu có
            movies['poster_url'] = movies['poster_url'].fillna('https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg')
            
            # Loại bỏ cột movie_id thừa sau khi merge
            if 'movie_id' in movies.columns:
                movies = movies.drop(columns=['movie_id'])
                
            print(f"Đã merge poster URLs. Số lượng phim có poster: {movies['poster_url'].ne('').sum()}")
        except Exception as e:
            print(f"⚠️ Không thể tải poster URLs: {e}")
            movies['poster_url'] = '' # Thêm cột rỗng nếu lỗi

        movies.to_sql('movies', engine, if_exists='append', index=False)
        print(f"Tải thành công {len(movies)} movies.")

        print("✅ Tải dữ liệu ban đầu hoàn tất!")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình tải dữ liệu: {e}")
        # Không exit(1) để container không restart liên tục nếu lỗi do duplicate key (khi chạy lại)
        # exit(1)

    # Tải Ratings
    print("Đang tải ratings.dat...")
    # Map columns: user_id, movie_id, rating, timestamp
    # id (PK) sẽ được tự động tạo bởi Postgres (SERIAL)
    r_cols = ['user_id', 'movie_id', 'rating', 'timestamp']
    ratings = pd.read_csv('data/ratings.dat', sep='::', names=r_cols, engine='python', encoding='latin-1')
    ratings.to_sql('ratings', engine, if_exists='append', index=False)
    print(f"Tải thành công {len(ratings)} ratings.")

if __name__ == "__main__":
    db_engine = wait_for_db()
    create_tables(db_engine)
    load_data(db_engine)