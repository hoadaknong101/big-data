# Hướng Dẫn Sử Dụng Hàm subscribe_user_events()

## Mô Tả
Hàm `subscribe_user_events()` được xây dựng để subscribe topic **user-events** từ Kafka và lưu tất cả message mới vào cơ sở dữ liệu PostgreSQL theo thời gian thực (real-time).

Hàm này sẽ:
- ✅ Chạy liên tục 24/7
- ✅ Lắng nghe topic `user-events` 
- ✅ Tự động xử lý và lưu message mới vào database
- ✅ Có khả năng recovery khi bị lỗi (checkpoint)
- ✅ Hiển thị log chi tiết về quá trình xử lý

## Cấu Trúc Dữ Liệu

### Input (Kafka Message)
Mỗi message trong topic `user-events` có cấu trúc JSON:
```json
{
  "user_id": 123,
  "movie_id": 456,
  "event_type": "click",
  "timestamp": 1701234567890
}
```

### Output (PostgreSQL Table)
Dữ liệu được lưu vào bảng `user_events` với các cột:
- `user_id` (INTEGER): ID người dùng
- `movie_id` (INTEGER): ID phim
- `event_type` (VARCHAR): Loại sự kiện (click, watch, etc.)
- `event_timestamp` (TIMESTAMP): Thời gian sự kiện xảy ra
- `processed_at` (TIMESTAMP): Thời gian xử lý và lưu vào database

## Chuẩn Bị Database

### Bước 1: Tạo Bảng user_events
Chạy SQL sau trong PostgreSQL để tạo bảng:

```sql
CREATE TABLE IF NOT EXISTS user_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index để tăng tốc độ truy vấn
CREATE INDEX idx_user_events_user_id ON user_events(user_id);
CREATE INDEX idx_user_events_movie_id ON user_events(movie_id);
CREATE INDEX idx_user_events_event_type ON user_events(event_type);
CREATE INDEX idx_user_events_timestamp ON user_events(event_timestamp);
```

### Bước 2: Kiểm Tra Bảng
```sql
-- Xem cấu trúc bảng
\d user_events

-- Kiểm tra dữ liệu
SELECT * FROM user_events ORDER BY processed_at DESC LIMIT 10;
```

## Cách Sử Dụng

### Option 1: Chạy Trực Tiếp Hàm subscribe_user_events()
Mở file `processor.py` và sửa phần cuối:

```python
if __name__ == "__main__":
    # Uncomment dòng bên dưới để chạy hàm subscribe_user_events
    subscribe_user_events()  # <-- Bỏ comment dòng này
    
    # Chạy hàm main gốc
    # main()  # <-- Comment dòng này lại
```

Sau đó chạy:
```bash
python processor.py
```

### Option 2: Chạy Từ Python Script Khác
```python
from processor import subscribe_user_events

# Gọi hàm để bắt đầu subscribe
subscribe_user_events()
```

### Option 3: Chạy Trong Docker
Nếu đang dùng Docker, cập nhật Dockerfile hoặc docker-compose.yml để gọi hàm mới.

## Giải Thích Chi Tiết Các Bước Xử Lý

### Bước 1: Khởi Tạo Spark Session
```python
spark = SparkSession.builder.appName("UserEventsSubscriber").getOrCreate()
```
- Tạo Spark Session để làm việc với Spark Streaming
- AppName giúp nhận diện ứng dụng trong Spark UI

### Bước 2: Kết Nối Kafka
```python
kafka_stream_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", "user-events") \
    .option("startingOffsets", "latest") \
    .load()
```
- `readStream`: Tạo streaming DataFrame
- `subscribe`: Subscribe topic "user-events"
- `startingOffsets="latest"`: Chỉ đọc message mới (không đọc lại message cũ)

### Bước 3: Định Nghĩa Schema
```python
user_events_schema = StructType([
    StructField("user_id", IntegerType(), True),
    StructField("movie_id", IntegerType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", LongType(), True),
])
```
- Schema giúp Spark hiểu cấu trúc dữ liệu JSON
- Tăng hiệu suất xử lý

### Bước 4: Parse JSON
```python
parsed_events_df = kafka_stream_df \
    .selectExpr("CAST(value AS STRING)") \
    .withColumn("data", from_json(col("value"), user_events_schema)) \
    .select("data.*")
```
- Chuyển đổi binary data thành string
- Parse JSON theo schema đã định nghĩa
- Extract các field ra thành columns

### Bước 5: Transform Data
```python
transformed_events_df = parsed_events_df \
    .withColumn("event_timestamp", col("timestamp").cast(TimestampType())) \
    .withColumn("processed_at", current_timestamp()) \
    .select("user_id", "movie_id", "event_type", "event_timestamp", "processed_at")
```
- Chuyển Unix timestamp sang TimestampType
- Thêm cột `processed_at` để tracking

### Bước 6: Định Nghĩa Hàm Ghi Database
```python
def write_user_events_to_postgres(batch_df, epoch_id):
    batch_df.write.format("jdbc") \
        .option("url", DB_URL) \
        .option("dbtable", "user_events") \
        .mode("append") \
        .save()
```
- Hàm này được gọi cho mỗi micro-batch
- `mode("append")`: Thêm dữ liệu mới, không ghi đè

### Bước 7: Bắt Đầu Streaming
```python
query = transformed_events_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_user_events_to_postgres) \
    .option("checkpointLocation", "/tmp/checkpoint/user-events") \
    .start()
```
- `outputMode("append")`: Chỉ ghi row mới
- `foreachBatch`: Xử lý từng batch
- `checkpointLocation`: Lưu trạng thái để recovery

### Bước 8: Chạy Liên Tục
```python
query.awaitTermination()
```
- Giữ chương trình chạy mãi mãi
- Chỉ dừng khi có lỗi hoặc Ctrl+C

## Monitoring & Debugging

### Xem Log Real-time
Khi chạy, bạn sẽ thấy output như:
```
============================================================
Bước 1: Khởi tạo Spark Session cho User Events Processing
============================================================
✓ Spark Session đã được khởi tạo thành công

============================================================
Bước 2: Kết nối tới Kafka và subscribe topic 'user-events'
============================================================
Kafka Broker: localhost:9092
Topic: user-events
✓ Đã kết nối thành công tới Kafka topic 'user-events'
...
```

### Khi Có Message Mới
```
============================================================
Epoch 5: Đang xử lý 3 records mới
============================================================
Sample data:
+-------+--------+----------+-------------------+-------------------+
|user_id|movie_id|event_type|event_timestamp    |processed_at       |
+-------+--------+----------+-------------------+-------------------+
|123    |456     |click     |2024-11-30 15:30:00|2024-11-30 15:30:05|
|124    |457     |watch     |2024-11-30 15:30:01|2024-11-30 15:30:05|
|125    |458     |click     |2024-11-30 15:30:02|2024-11-30 15:30:05|
+-------+--------+----------+-------------------+-------------------+
✓ Đã ghi thành công 3 records vào bảng user_events
============================================================
```

### Kiểm Tra Database
```sql
-- Xem tổng số events
SELECT COUNT(*) FROM user_events;

-- Xem events theo loại
SELECT event_type, COUNT(*) 
FROM user_events 
GROUP BY event_type;

-- Xem events mới nhất
SELECT * FROM user_events 
ORDER BY processed_at DESC 
LIMIT 10;

-- Xem events của một user cụ thể
SELECT * FROM user_events 
WHERE user_id = 123 
ORDER BY event_timestamp DESC;
```

## Xử Lý Lỗi

### Lỗi Kết Nối Kafka
```
Lỗi: Failed to construct kafka consumer
```
**Giải pháp**: Kiểm tra KAFKA_BROKER trong biến môi trường

### Lỗi Kết Nối Database
```
Lỗi: Connection refused
```
**Giải pháp**: 
1. Kiểm tra PostgreSQL đang chạy
2. Kiểm tra thông tin kết nối (host, port, user, password)
3. Kiểm tra firewall

### Lỗi Bảng Không Tồn Tại
```
Lỗi: relation "user_events" does not exist
```
**Giải pháp**: Chạy SQL tạo bảng ở phần "Chuẩn Bị Database"

## Environment Variables Cần Thiết

Đảm bảo các biến môi trường sau được set:
```bash
KAFKA_BROKER=localhost:9092
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_DB=your_database
```

## Performance Tips

1. **Batch Size**: Spark tự động batch messages, mặc định là vài giây
2. **Checkpoint**: Lưu ở `/tmp/checkpoint/user-events`, có thể thay đổi
3. **Parallelism**: Spark tự động phân tán xử lý
4. **Index**: Đã tạo index trên các cột quan trọng để tăng tốc query

## So Sánh Với Hàm main() Gốc

| Tính năng | main() | subscribe_user_events() |
|-----------|--------|-------------------------|
| Topic | Configurable (KAFKA_TOPIC) | Fixed: user-events |
| Filter | Chỉ lưu event_type="click" | Lưu TẤT CẢ events |
| Target Table | ratings | user_events |
| Columns | user_id, movie_id, rating, timestamp | user_id, movie_id, event_type, event_timestamp, processed_at |
| Comments | Ít | Chi tiết từng bước |

## Tóm Tắt

✅ Hàm `subscribe_user_events()` đã được xây dựng hoàn chỉnh
✅ Subscribe topic `user-events` real-time
✅ Lưu TẤT CẢ message vào database
✅ Comment chi tiết từng bước bằng tiếng Việt
✅ Có xử lý lỗi và logging đầy đủ
✅ Chạy liên tục 24/7 và đợi message mới
