import os
import time
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from dotenv import load_dotenv

load_dotenv()

# --- Configs ---
# DB
DB_USER = "admin"
DB_PASSWORD = "admin"
DB_HOST = "127.0.0.1"
DB_NAME = "movielens"
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
print(DB_URL)

# Milvus
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"
print(MILVUS_HOST, MILVUS_PORT)

# Model
EMBEDDING_DIM = 32 # Kích thước vector embedding
EPOCHS = 1
BATCH_SIZE = 1024
LEARNING_RATE = 0.005

# Milvus Collection Names
USER_COLLECTION = "user_embeddings"
MOVIE_COLLECTION = "movie_embeddings"

# --- PyTorch Model ---
# Chúng ta không dùng GPU trong demo này, chỉ dùng CPU
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

class MovieLensDataset(Dataset):
    def __init__(self, users, movies, ratings):
        self.users = users
        self.movies = movies
        self.ratings = ratings
    
    def __len__(self):
        return len(self.ratings)
    
    def __getitem__(self, idx):
        return self.users[idx], self.movies[idx], self.ratings[idx]

class MatrixFactorization(nn.Module):
    def __init__(self, num_users, num_movies, n_factors):
        super().__init__()
        self.user_factors = nn.Embedding(num_users, n_factors, sparse=False)
        self.movie_factors = nn.Embedding(num_movies, n_factors, sparse=False)
    
    def forward(self, user, movie):
        return (self.user_factors(user) * self.movie_factors(movie)).sum(1)

def wait_for_service(host, port, service_name):
    """Chờ một service sẵn sàng."""
    print(f"Đang chờ {service_name} ({host}:{port}) sẵn sàng...")
    retries = 10
    while retries > 0:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, int(port)))
            sock.close()
            print(f"✅ {service_name} đã sẵn sàng!")
            return
        except Exception as e:
            print(f"Lỗi kết nối {service_name}: {e}. Thử lại sau 5s...")
            retries -= 1
            time.sleep(5)
    print(f"❌ Không thể kết nối tới {service_name}.")
    exit(1)

def connect_db():
    print("Đang kết nối tới Postgres...")
    engine = create_engine(DB_URL)
    return engine

def connect_milvus():
    print("Đang kết nối tới Milvus...")
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    print("✅ Kết nối Milvus thành công.")

def create_milvus_collections():
    """Tạo collection (schema) trong Milvus."""
    
    # Xóa collection cũ nếu tồn tại
    if utility.has_collection(USER_COLLECTION):
        utility.drop_collection(USER_COLLECTION)
    if utility.has_collection(MOVIE_COLLECTION):
        utility.drop_collection(MOVIE_COLLECTION)

    # --- User Collection ---
    user_fields = [
        FieldSchema(name="user_id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    ]
    user_schema = CollectionSchema(user_fields, "User Embeddings")
    user_collection = Collection(USER_COLLECTION, user_schema)
    print(f"Tạo collection {USER_COLLECTION} thành công.")

    # --- Movie Collection ---
    movie_fields = [
        FieldSchema(name="movie_id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
    ]
    movie_schema = CollectionSchema(movie_fields, "Movie Embeddings")
    movie_collection = Collection(MOVIE_COLLECTION, movie_schema)
    print(f"Tạo collection {MOVIE_COLLECTION} thành công.")

    # --- Tạo Index cho Movie (để tìm kiếm) ---
    index_params = {
        "metric_type": "L2", # Khoảng cách Euclidean
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    movie_collection.create_index("embedding", index_params)
    print("Tạo index cho movie embeddings thành công.")

    # --- Tạo Index cho User ---
    user_collection.create_index("embedding", index_params)
    print("Tạo index cho user embeddings thành công.")
    
    return user_collection, movie_collection

def train_model(engine):
    """Huấn luyện mô hình MF."""
    print("Đang tải dữ liệu ratings từ Postgres...")
    ratings_df = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", engine)

    # Convert ID sang index liên tục (0-N)
    user_ids = ratings_df['user_id'].unique()
    movie_ids = ratings_df['movie_id'].unique()
    
    user_map = {id: i for i, id in enumerate(user_ids)}
    movie_map = {id: i for i, id in enumerate(movie_ids)}
    
    ratings_df['user_idx'] = ratings_df['user_id'].map(user_map)
    ratings_df['movie_idx'] = ratings_df['movie_id'].map(movie_map)
    
    num_users = len(user_ids)
    num_movies = len(movie_ids)

    print(f"Bắt đầu huấn luyện mô hình cho {num_users} users và {num_movies} movies...")

    # Chuẩn bị data
    users = torch.LongTensor(ratings_df.user_idx.values)
    movies = torch.LongTensor(ratings_df.movie_idx.values)
    ratings = torch.FloatTensor(ratings_df.rating.values)
    
    dataset = MovieLensDataset(users, movies, ratings)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # Model
    model = MatrixFactorization(num_users, num_movies, EMBEDDING_DIM)
    loss_fn = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training loop
    for epoch in range(EPOCHS):
        start_time = time.time()
        total_loss = 0
        for u, m, r in dataloader:
            optimizer.zero_grad()
            predictions = model(u, m)
            loss = loss_fn(predictions, r)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        epoch_time = time.time() - start_time
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{EPOCHS} - Loss: {avg_loss:.4f} - Time: {epoch_time:.2f}s")
        
    print("✅ Huấn luyện hoàn tất.")
    
    # Lấy embeddings
    user_embeddings = model.user_factors.weight.data.cpu().numpy()
    movie_embeddings = model.movie_factors.weight.data.cpu().numpy()
    
    return user_embeddings, movie_embeddings, user_map, movie_map

def ingest_to_milvus(user_collection, movie_collection, user_embeddings, movie_embeddings, user_map, movie_map):
    """Nạp embeddings vào Milvus."""
    print("Bắt đầu nạp (ingest) embeddings vào Milvus...")
    
    # --- Ingest Users ---
    # Đảo ngược map: index -> user_id
    user_idx_to_id = {i: id for id, i in user_map.items()}
    
    user_data = [
        {"user_id": user_idx_to_id[i], "embedding": user_embeddings[i]}
        for i in range(len(user_embeddings))
    ]
    user_collection.insert(user_data)
    print(f"Nạp thành công {len(user_data)} user embeddings.")
    
    # --- Ingest Movies ---
    movie_idx_to_id = {i: id for id, i in movie_map.items()}
    
    movie_data = [
        {"movie_id": movie_idx_to_id[i], "embedding": movie_embeddings[i]}
        for i in range(len(movie_embeddings))
    ]
    movie_collection.insert(movie_data)
    print(f"Nạp thành công {len(movie_data)} movie embeddings.")
    
    # Flush để đảm bảo dữ liệu được ghi
    user_collection.flush()
    movie_collection.flush()
    
    # Load collection vào bộ nhớ để tìm kiếm
    user_collection.load()
    movie_collection.load()
    print("✅ Nạp Milvus hoàn tất.")

def train_and_ingest():
    try:
        wait_for_service(DB_HOST, 5432, "Postgres")
        wait_for_service(MILVUS_HOST, 19530, "Milvus")
    
        db_engine = connect_db()
        connect_milvus()
    
        user_col, movie_col = create_milvus_collections()
    
        u_embeds, m_embeds, u_map, m_map = train_model(db_engine)
    
        ingest_to_milvus(user_col, movie_col, u_embeds, m_embeds, u_map, m_map)

        return True
    except Exception as e:
        print(f"Error training and ingesting: {str(e)}")
        return False

if __name__ == "__main__":
    wait_for_service(DB_HOST, 5432, "Postgres")
    wait_for_service(MILVUS_HOST, 19530, "Milvus")
    
    db_engine = connect_db()
    connect_milvus()
    
    user_col, movie_col = create_milvus_collections()
    
    u_embeds, m_embeds, u_map, m_map = train_model(db_engine)
    
    ingest_to_milvus(user_col, movie_col, u_embeds, m_embeds, u_map, m_map)