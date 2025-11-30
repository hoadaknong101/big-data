# Tóm Tắt Công Việc Hoàn Thành

## 📋 Yêu Cầu
Xây dựng hàm thực hiện subscribe topic `user-events` từ Kafka, lưu message mới vào database real-time với comment chi tiết.

## ✅ Đã Hoàn Thành

### 1. File `processor.py` - Hàm Chính
**Đã thêm hàm `subscribe_user_events()`** với các tính năng:

#### 🔹 Bước 1: Khởi tạo Spark Session
```python
spark = SparkSession.builder.appName("UserEventsSubscriber").getOrCreate()
```
- Tạo Spark Session để xử lý streaming data
- Set log level = WARN để giảm nhiễu

#### 🔹 Bước 2: Kết nối Kafka và Subscribe Topic
```python
kafka_stream_df = spark.readStream \
    .format("kafka") \
    .option("subscribe", "user-events") \
    .option("startingOffsets", "latest") \
    .load()
```
- Subscribe topic `user-events` 
- Chỉ đọc message mới (latest)
- Tạo streaming DataFrame

#### 🔹 Bước 3: Định nghĩa Schema
```python
user_events_schema = StructType([
    StructField("user_id", IntegerType(), True),
    StructField("movie_id", IntegerType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", LongType(), True),
])
```
- Schema cho JSON message
- Tăng hiệu suất parsing

#### 🔹 Bước 4: Parse JSON từ Kafka Message
```python
parsed_events_df = kafka_stream_df \
    .selectExpr("CAST(value AS STRING)") \
    .withColumn("data", from_json(col("value"), user_events_schema)) \
    .select("data.*")
```
- Chuyển binary → string
- Parse JSON theo schema
- Extract fields

#### 🔹 Bước 5: Transform Data
```python
transformed_events_df = parsed_events_df \
    .withColumn("event_timestamp", col("timestamp").cast(TimestampType())) \
    .withColumn("processed_at", current_timestamp()) \
    .select("user_id", "movie_id", "event_type", "event_timestamp", "processed_at")
```
- Convert Unix timestamp → TimestampType
- Thêm cột `processed_at`

#### 🔹 Bước 6: Hàm Ghi Database
```python
def write_user_events_to_postgres(batch_df, epoch_id):
    batch_df.write.format("jdbc") \
        .option("dbtable", "user_events") \
        .mode("append") \
        .save()
```
- Ghi từng micro-batch vào PostgreSQL
- Mode append (không ghi đè)
- Hiển thị sample data

#### 🔹 Bước 7: Bắt đầu Streaming
```python
query = transformed_events_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_user_events_to_postgres) \
    .option("checkpointLocation", "/tmp/checkpoint/user-events") \
    .start()
```
- Start streaming query
- Checkpoint để recovery
- foreachBatch processing

#### 🔹 Bước 8: Chạy Liên Tục
```python
query.awaitTermination()
```
- Chạy 24/7
- Đợi message mới
- Xử lý exception (Ctrl+C, errors)

### 2. File `setup_user_events_table.sql` - Database Schema
**Script SQL hoàn chỉnh** bao gồm:

```sql
CREATE TABLE user_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes** để tăng tốc:
- `idx_user_events_user_id`
- `idx_user_events_movie_id`
- `idx_user_events_event_type`
- `idx_user_events_timestamp`
- Composite indexes

**Helper Functions**:
- `get_recent_events(limit)` - Xem events mới nhất
- `get_user_events(user_id, limit)` - Xem events của user

**View**:
- `user_events_stats` - Thống kê nhanh

### 3. File `run_user_events_subscriber.py` - Script Chạy
**Standalone script** với:
- ✅ Kiểm tra environment variables
- ✅ Error handling
- ✅ Hướng dẫn khắc phục lỗi
- ✅ Graceful shutdown (Ctrl+C)

### 4. File `README_USER_EVENTS.md` - Tài Liệu
**Documentation đầy đủ** bao gồm:
- 📖 Giải thích chi tiết từng bước
- 🚀 Hướng dẫn sử dụng (3 options)
- 🔍 Monitoring & debugging
- 🛠️ Troubleshooting
- 📊 Performance tips
- 📝 Sample queries

## 🎯 Tính Năng Chính

### ✨ Real-time Processing
- Chạy liên tục 24/7
- Tự động xử lý message mới
- Latency thấp (vài giây)

### 🔄 Fault Tolerance
- Checkpoint mechanism
- Auto recovery khi lỗi
- Không mất dữ liệu

### 📊 Monitoring
- Log chi tiết từng bước
- Hiển thị sample data
- Thống kê real-time

### 💾 Data Storage
- Lưu TẤT CẢ events (không filter)
- Append mode (không ghi đè)
- Index tối ưu cho query

## 📁 Cấu Trúc Files

```
spark_processor/
├── processor.py                      # ✅ Code chính (đã update)
├── run_user_events_subscriber.py     # ✅ Script chạy
├── setup_user_events_table.sql       # ✅ Database setup
├── README_USER_EVENTS.md             # ✅ Documentation
├── requirements.txt                  # Existing
└── Dockerfile                        # Existing
```

## 🚀 Cách Sử Dụng Nhanh

### Bước 1: Setup Database
```bash
psql -U your_user -d your_database -f setup_user_events_table.sql
```

### Bước 2: Set Environment Variables
```bash
export KAFKA_BROKER=localhost:9092
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_DB=your_database
```

### Bước 3: Chạy Subscriber
**Option A**: Dùng script standalone
```bash
python run_user_events_subscriber.py
```

**Option B**: Sửa processor.py
```python
if __name__ == "__main__":
    subscribe_user_events()  # Uncomment dòng này
    # main()  # Comment dòng này
```
Rồi chạy:
```bash
python processor.py
```

## 📊 Data Flow

```
Kafka Topic (user-events)
    ↓
Spark Streaming (subscribe_user_events)
    ↓
Parse JSON + Transform
    ↓
PostgreSQL (user_events table)
```

## 🔍 Monitoring Queries

```sql
-- Tổng số events
SELECT COUNT(*) FROM user_events;

-- Events theo loại
SELECT * FROM user_events_stats;

-- 10 events mới nhất
SELECT * FROM get_recent_events(10);

-- Events của user 123
SELECT * FROM get_user_events(123);
```

## 💡 Điểm Nổi Bật

### 1. Comment Chi Tiết
✅ Mỗi bước có comment giải thích bằng tiếng Việt
✅ Giải thích tại sao (why), không chỉ là gì (what)
✅ Code dễ hiểu cho người mới

### 2. Production-Ready
✅ Error handling đầy đủ
✅ Checkpoint cho fault tolerance
✅ Logging chi tiết
✅ Performance optimization (indexes)

### 3. Developer-Friendly
✅ Documentation đầy đủ
✅ Helper scripts
✅ Sample queries
✅ Troubleshooting guide

## 🎓 Kiến Thức Áp Dụng

### Spark Streaming
- ✅ readStream API
- ✅ Structured Streaming
- ✅ foreachBatch processing
- ✅ Checkpoint mechanism

### Kafka Integration
- ✅ Subscribe topic
- ✅ Parse Kafka message
- ✅ Offset management

### Data Processing
- ✅ JSON parsing với schema
- ✅ Data transformation
- ✅ Type casting

### Database
- ✅ JDBC connection
- ✅ Batch writing
- ✅ Index optimization

## 🏆 Kết Quả

✅ **Hàm `subscribe_user_events()` hoàn chỉnh**
- Subscribe topic `user-events` ✓
- Lưu real-time vào database ✓
- Comment chi tiết từng bước ✓
- Chạy liên tục 24/7 ✓

✅ **Database schema đầy đủ**
- Table với indexes ✓
- Helper functions ✓
- Stats view ✓

✅ **Documentation hoàn chỉnh**
- Hướng dẫn sử dụng ✓
- Troubleshooting ✓
- Sample queries ✓

✅ **Production-ready code**
- Error handling ✓
- Fault tolerance ✓
- Monitoring ✓

---

**Tất cả yêu cầu đã được hoàn thành!** 🎉
