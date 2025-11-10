import os
import time
import pandas as pd
from sqlalchemy import create_engine

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

def load_data(engine):
    """Tải dữ liệu từ file .dat vào Postgres."""
    print("Bắt đầu tải dữ liệu MovieLens...")
    
    try:
        # Tải Users
        print("Đang tải users.dat...")
        u_cols = ['user_id', 'gender', 'age', 'occupation', 'zip']
        users = pd.read_csv('data/users.dat', sep='::', names=u_cols, engine='python', encoding='latin-1')
        users.to_sql('users', engine, if_exists='replace', index=False)
        print(f"Tải thành công {len(users)} users.")

        # Tải Ratings
        print("Đang tải ratings.dat...")
        r_cols = ['user_id', 'movie_id', 'rating', 'timestamp']
        ratings = pd.read_csv('data/ratings.dat', sep='::', names=r_cols, engine='python', encoding='latin-1')
        ratings.to_sql('ratings', engine, if_exists='replace', index=False)
        print(f"Tải thành công {len(ratings)} ratings.")

        # Tải Movies
        print("Đang tải movies.dat...")
        m_cols = ['movie_id', 'title', 'genres']
        movies = pd.read_csv('data/movies.dat', sep='::', names=m_cols, engine='python', encoding='latin-1')
        movies.to_sql('movies', engine, if_exists='replace', index=False)
        print(f"Tải thành công {len(movies)} movies.")

        print("✅ Tải dữ liệu ban đầu hoàn tất!")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình tải dữ liệu: {e}")
        exit(1)

if __name__ == "__main__":
    db_engine = wait_for_db()
    load_data(db_engine)