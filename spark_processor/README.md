# Spark Processor - User Events Real-time Streaming

## 📖 Giới Thiệu

Dự án này cung cấp một hệ thống xử lý streaming real-time sử dụng **Apache Spark Structured Streaming** để subscribe topic `user-events` từ **Kafka** và lưu trữ dữ liệu vào **PostgreSQL**.

### Tính Năng Chính
- ✅ **Real-time Processing**: Xử lý dữ liệu theo thời gian thực
- ✅ **Fault Tolerance**: Checkpoint mechanism để recovery khi lỗi
- ✅ **Scalable**: Có thể scale horizontal với Kafka partitions
- ✅ **Production-Ready**: Error handling, logging, monitoring đầy đủ
- ✅ **Well-Documented**: Comment chi tiết từng bước bằng tiếng Việt

---

## 📁 Cấu Trúc Thư Mục

```
spark_processor/
├── processor.py                      # ⭐ Code chính - Hàm subscribe_user_events()
├── run_user_events_subscriber.py     # 🚀 Script để chạy subscriber
├── setup_user_events_table.sql       # 🗄️ SQL script tạo database schema
├── README_USER_EVENTS.md             # 📖 Documentation chi tiết
├── ARCHITECTURE.md                   # 🏗️ Sơ đồ kiến trúc hệ thống
├── SUMMARY.md                        # 📝 Tóm tắt công việc
├── QUICK_REFERENCE.md                # 📋 Quick reference guide
├── requirements.txt                  # 📦 Python dependencies
├── Dockerfile                        # 🐳 Docker configuration
└── README.md                         # 📄 File này
```

---

## 🚀 Quick Start

### Bước 1: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Setup Database
```bash
psql -U postgres -d your_database -f setup_user_events_table.sql
```

### Bước 3: Set Environment Variables
```bash
export KAFKA_BROKER=localhost:9092
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_DB=your_database
```

### Bước 4: Chạy Subscriber
```bash
python run_user_events_subscriber.py
```

---

## 📚 Documentation

### 1. [README_USER_EVENTS.md](README_USER_EVENTS.md)
**Hướng dẫn chi tiết** về:
- Cách sử dụng hàm `subscribe_user_events()`
- Giải thích từng bước xử lý
- Monitoring & debugging
- Troubleshooting
- Performance tips

### 2. [ARCHITECTURE.md](ARCHITECTURE.md)
**Sơ đồ kiến trúc** bao gồm:
- Data flow diagram
- Processing timeline
- Fault tolerance mechanism
- Scaling strategy
- Monitoring points

### 3. [SUMMARY.md](SUMMARY.md)
**Tóm tắt công việc** đã hoàn thành:
- Các tính năng đã implement
- Cấu trúc code
- Kết quả đạt được

### 4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Quick reference** cho:
- Common commands
- SQL queries
- Debugging tips
- Configuration options

---

## 🎯 Hàm Chính: `subscribe_user_events()`

### Mô Tả
Hàm này subscribe topic `user-events` từ Kafka và lưu **TẤT CẢ** message vào PostgreSQL real-time.

### Các Bước Xử Lý

#### 1️⃣ Khởi tạo Spark Session
```python
spark = SparkSession.builder.appName("UserEventsSubscriber").getOrCreate()
```

#### 2️⃣ Kết nối Kafka
```python
kafka_stream_df = spark.readStream \
    .format("kafka") \
    .option("subscribe", "user-events") \
    .option("startingOffsets", "latest") \
    .load()
```

#### 3️⃣ Định nghĩa Schema
```python
user_events_schema = StructType([
    StructField("user_id", IntegerType(), True),
    StructField("movie_id", IntegerType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", LongType(), True),
])
```

#### 4️⃣ Parse JSON
```python
parsed_events_df = kafka_stream_df \
    .selectExpr("CAST(value AS STRING)") \
    .withColumn("data", from_json(col("value"), user_events_schema)) \
    .select("data.*")
```

#### 5️⃣ Transform Data
```python
transformed_events_df = parsed_events_df \
    .withColumn("event_timestamp", col("timestamp").cast(TimestampType())) \
    .withColumn("processed_at", current_timestamp())
```

#### 6️⃣ Write to PostgreSQL
```python
def write_user_events_to_postgres(batch_df, epoch_id):
    batch_df.write.format("jdbc") \
        .option("dbtable", "user_events") \
        .mode("append") \
        .save()
```

#### 7️⃣ Start Streaming
```python
query = transformed_events_df.writeStream \
    .outputMode("append") \
    .foreachBatch(write_user_events_to_postgres) \
    .option("checkpointLocation", "/tmp/checkpoint/user-events") \
    .start()
```

#### 8️⃣ Await Termination
```python
query.awaitTermination()
```

---

## 🗄️ Database Schema

### Table: `user_events`
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

### Indexes
- `idx_user_events_user_id` - Query by user
- `idx_user_events_movie_id` - Query by movie
- `idx_user_events_event_type` - Filter by event type
- `idx_user_events_timestamp` - Query by time
- Composite indexes for common queries

### Views
- `user_events_stats` - Statistics by event type

### Functions
- `get_recent_events(limit)` - Get recent events
- `get_user_events(user_id, limit)` - Get user's events

---

## 📊 Data Flow

```
Web Client → API Gateway → Kafka (user-events) → Spark Streaming → PostgreSQL
```

### Input (Kafka Message)
```json
{
  "user_id": 123,
  "movie_id": 456,
  "event_type": "click",
  "timestamp": 1701234567890
}
```

### Output (PostgreSQL Record)
```
id | user_id | movie_id | event_type | event_timestamp      | processed_at         | created_at
---+---------+----------+------------+---------------------+----------------------+----------------------
1  | 123     | 456      | click      | 2024-11-30 15:30:00 | 2024-11-30 15:30:05 | 2024-11-30 15:30:05
```

---

## 🔍 Monitoring

### Xem Events Mới Nhất
```sql
SELECT * FROM user_events ORDER BY processed_at DESC LIMIT 10;
```

### Thống Kê
```sql
SELECT * FROM user_events_stats;
```

### Processing Rate
```sql
SELECT 
    DATE_TRUNC('minute', processed_at) as minute,
    COUNT(*) as events_processed
FROM user_events
WHERE processed_at > NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC;
```

---

## 🛠️ Troubleshooting

### Kafka Connection Error
```bash
# Kiểm tra Kafka đang chạy
docker ps | grep kafka

# Kiểm tra topic
kafka-topics --list --bootstrap-server localhost:9092
```

### PostgreSQL Connection Error
```bash
# Kiểm tra PostgreSQL đang chạy
docker ps | grep postgres

# Test connection
psql -U postgres -h localhost -d your_database
```

### Table Not Found Error
```sql
-- Tạo lại bảng
\i setup_user_events_table.sql
```

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `KAFKA_BROKER` | Kafka server address | `localhost:9092` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `your_password` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_DB` | Database name | `your_database` |

### Spark Configuration
```python
# Thay đổi checkpoint location
.option("checkpointLocation", "/custom/path")

# Thay đổi starting offset
.option("startingOffsets", "earliest")  # Đọc từ đầu
.option("startingOffsets", "latest")    # Chỉ đọc mới
```

---

## 🎓 Kiến Thức Cần Thiết

### Technologies
- **Apache Spark**: Distributed processing framework
- **Kafka**: Distributed streaming platform
- **PostgreSQL**: Relational database
- **PySpark**: Python API for Spark

### Concepts
- **Structured Streaming**: Spark's streaming API
- **Micro-batching**: Processing data in small batches
- **Checkpoint**: Saving state for fault tolerance
- **foreachBatch**: Processing each batch with custom logic
- **JDBC**: Java Database Connectivity

---

## 📈 Performance Tips

1. **Kafka Partitions**: Tăng số partitions để scale horizontal
2. **Batch Interval**: Điều chỉnh processing time phù hợp
3. **Database Indexes**: Đã tạo sẵn indexes cho performance
4. **Checkpoint Cleanup**: Xóa checkpoint cũ khi thay đổi schema
5. **Monitoring**: Theo dõi lag và processing time

---

## 🔒 Security

### Best Practices
- ✅ Không commit password vào git
- ✅ Sử dụng environment variables
- ✅ Encrypt database connections (SSL)
- ✅ Limit database user permissions
- ✅ Monitor access logs

---

## 🧪 Testing

### Test với Sample Data
```bash
# Produce test message to Kafka
echo '{"user_id":123,"movie_id":456,"event_type":"click","timestamp":1701234567890}' | \
  kafka-console-producer --topic user-events --bootstrap-server localhost:9092
```

### Verify in Database
```sql
SELECT * FROM user_events WHERE user_id = 123;
```

---

## 🐳 Docker Support

### Build Image
```bash
docker build -t spark-processor .
```

### Run Container
```bash
docker run -e KAFKA_BROKER=kafka:9092 \
           -e POSTGRES_HOST=postgres \
           -e POSTGRES_USER=postgres \
           -e POSTGRES_PASSWORD=password \
           -e POSTGRES_DB=mydb \
           spark-processor
```

---

## 📞 Support

### Tài Liệu
- [README_USER_EVENTS.md](README_USER_EVENTS.md) - Hướng dẫn chi tiết
- [ARCHITECTURE.md](ARCHITECTURE.md) - Kiến trúc hệ thống
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference

### Common Issues
- Xem phần Troubleshooting trong [README_USER_EVENTS.md](README_USER_EVENTS.md)
- Xem logs trong console output
- Check Spark UI tại `http://localhost:4040`

---

## 📝 License

This project is for educational purposes.

---

## 👥 Contributors

- Developed for Big Data course project
- Detailed Vietnamese comments for learning purposes

---

## 🎉 Kết Luận

Hệ thống này cung cấp một giải pháp hoàn chỉnh cho việc xử lý streaming data real-time từ Kafka vào PostgreSQL sử dụng Spark Structured Streaming. Code được viết với comment chi tiết bằng tiếng Việt để dễ hiểu và học tập.

**Happy Streaming! 🚀**
