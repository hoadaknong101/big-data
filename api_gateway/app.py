import os
import json
import time
from flask import Flask, request, jsonify
from pymilvus import connections, Collection, utility
from kafka import KafkaProducer
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('POSTGRES_HOST')
DB_NAME = os.environ.get('POSTGRES_DB')
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'

MILVUS_HOST = os.environ.get('MILVUS_HOST')
MILVUS_PORT = os.environ.get('MILVUS_PORT')

KAFKA_BROKER = os.environ.get('KAFKA_BROKER')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC')

USER_COLLECTION = "user_embeddings"
MOVIE_COLLECTION = "movie_embeddings"

# --- Khởi tạo ---
app = Flask(__name__)

# Kết nối Postgres
try:
    db_engine = create_engine(DB_URL)
    print("✅ API kết nối Postgres thành công.")
except Exception as e:
    print(f"❌ API lỗi kết nối Postgres: {e}")

# Kết nối Milvus
user_collection = None
movie_collection = None

try:
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    # Load collection
    if utility.has_collection(USER_COLLECTION):
        user_collection = Collection(USER_COLLECTION)
        user_collection.load()
    if utility.has_collection(MOVIE_COLLECTION):
        movie_collection = Collection(MOVIE_COLLECTION)
        movie_collection.load()
    print("✅ API kết nối và load Milvus collection thành công.")
except Exception as e:
    print(f"❌ API lỗi kết nối Milvus: {e}")

# Kết nối Kafka
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✅ API kết nối Kafka Producer thành công.")
except Exception as e:
    print(f"❌ API lỗi kết nối Kafka: {e}")


# --- API Endpoints ---

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route("/recommendations/<int:user_id>", methods=['GET'])
def get_recommendations(user_id):
    """
    Lấy gợi ý cho 1 user:
    1. Lấy user embedding từ Milvus.
    2. Dùng user embedding để tìm 10 movie embedding gần nhất (ANN search).
    3. Lấy thông tin (title) của 10 movie đó từ Postgres.
    """
    try:
        if user_collection is None or movie_collection is None:
             return jsonify({"error": "Milvus collection not initialized"}), 503

        # 1. Lấy user embedding
        # Truy vấn (query) để lấy embedding của user_id cụ thể
        res = user_collection.query(
            expr=f"user_id == {user_id}",
            output_fields=["embedding"]
        )
        
        if not res:
            return jsonify({"error": f"User ID {user_id} không tìm thấy embedding."}), 404
   
        user_vector = res[0]['embedding']
        
        # 2. Tìm kiếm (search) movie gần nhất
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        search_results = movie_collection.search(
            data=[user_vector],
            anns_field="embedding",
            param=search_params,
            limit=20,
            output_fields=["movie_id"]
        )
        
        # 3. Lấy thông tin movie từ Postgres
        movie_ids = [hit.entity.get('movie_id') for hit in search_results[0]]
        
        if not movie_ids:
            return jsonify({"recommendations": []}), 200
            
        # Tạo câu truy vấn SQL an toàn
        ids_tuple = tuple(movie_ids)
        query = f"SELECT id, title, genres FROM movies WHERE id IN {ids_tuple}"
        
        movie_details_df = pd.read_sql(query, db_engine)
        
        # Sắp xếp kết quả theo thứ tự trả về từ Milvus
        movie_details_df['id'] = movie_details_df['id'].astype('category')
        movie_details_df['id'] = movie_details_df['id'].cat.set_categories(movie_ids)
        movie_details_df = movie_details_df.sort_values('id')
        
        return jsonify(movie_details_df.to_dict('records')), 200

    except Exception as e:
        print(f"Lỗi khi lấy gợi ý: {e}")
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route("/event", methods=['POST'])
def post_event():
    """
    Nhận 1 sự kiện (ví dụ: click) và đẩy vào Kafka.
    Payload: {"user_id": 123, "movie_id": 456, "event_type": "click"}
    """
    try:
        data = request.json
        if not data or 'user_id' not in data or 'movie_id' not in data:
            return jsonify({"error": "Payload không hợp lệ."}), 400
            
        # Thêm timestamp
        data['timestamp'] = int(time.time())
        
        # Gửi tới Kafka
        if producer:
            producer.send(KAFKA_TOPIC, value=data)
            producer.flush()
            print("✅ Event sent to Kafka.")
            return jsonify({"status": "event received"}), 201
        else:
            print("❌ Kafka producer not initialized.")
            return jsonify({"error": "Kafka producer not initialized"}), 503
        
    except Exception as e:
        print(f"Lỗi khi gửi sự kiện: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)