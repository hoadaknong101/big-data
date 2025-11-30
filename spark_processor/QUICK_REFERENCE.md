# Quick Reference - User Events Subscriber

## 🚀 Chạy Nhanh (Quick Start)

### 1. Setup Database
```bash
psql -U postgres -d your_db -f setup_user_events_table.sql
```

### 2. Set Environment
```bash
export KAFKA_BROKER=localhost:9092
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_DB=your_database
```

### 3. Run Subscriber
```bash
python run_user_events_subscriber.py
```

---

## 📝 Code Snippets

### Import và Gọi Hàm
```python
from processor import subscribe_user_events

# Chạy subscriber
subscribe_user_events()
```

### Kiểm Tra Environment
```python
import os
print(f"Kafka: {os.environ.get('KAFKA_BROKER')}")
print(f"DB: {os.environ.get('POSTGRES_HOST')}")
```

---

## 🗄️ SQL Queries

### Xem Tất Cả Events
```sql
SELECT * FROM user_events ORDER BY processed_at DESC LIMIT 10;
```

### Đếm Events
```sql
SELECT COUNT(*) FROM user_events;
```

### Thống Kê Theo Event Type
```sql
SELECT * FROM user_events_stats;
```

### Events Của User
```sql
SELECT * FROM get_user_events(123, 50);
```

### Events Mới Nhất
```sql
SELECT * FROM get_recent_events(10);
```

### Events Trong 1 Giờ Qua
```sql
SELECT * FROM user_events 
WHERE event_timestamp > NOW() - INTERVAL '1 hour'
ORDER BY event_timestamp DESC;
```

### Top Users
```sql
SELECT user_id, COUNT(*) as event_count
FROM user_events
GROUP BY user_id
ORDER BY event_count DESC
LIMIT 10;
```

### Top Movies
```sql
SELECT movie_id, COUNT(*) as interaction_count
FROM user_events
GROUP BY movie_id
ORDER BY interaction_count DESC
LIMIT 10;
```

---

## 🔍 Debugging Commands

### Kiểm Tra Kafka
```bash
# List topics
kafka-topics --list --bootstrap-server localhost:9092

# Describe topic
kafka-topics --describe --topic user-events --bootstrap-server localhost:9092

# Consume messages
kafka-console-consumer --topic user-events --from-beginning --bootstrap-server localhost:9092
```

### Kiểm Tra PostgreSQL
```bash
# Connect
psql -U postgres -d your_db

# List tables
\dt

# Describe table
\d user_events

# Check connections
SELECT * FROM pg_stat_activity WHERE datname = 'your_db';
```

### Kiểm Tra Spark
```bash
# Check if running
ps aux | grep spark

# View logs
tail -f /path/to/spark/logs/spark-*.log
```

---

## 🛠️ Troubleshooting

### Lỗi: Connection refused (Kafka)
```bash
# Kiểm tra Kafka đang chạy
docker ps | grep kafka

# Restart Kafka
docker restart kafka
```

### Lỗi: Connection refused (PostgreSQL)
```bash
# Kiểm tra PostgreSQL đang chạy
docker ps | grep postgres

# Restart PostgreSQL
docker restart postgres
```

### Lỗi: Table does not exist
```sql
-- Tạo lại bảng
\i setup_user_events_table.sql
```

### Lỗi: Permission denied
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE user_events TO your_user;
GRANT USAGE, SELECT ON SEQUENCE user_events_id_seq TO your_user;
```

---

## 📊 Monitoring

### Xem Processing Rate
```sql
SELECT 
    DATE_TRUNC('minute', processed_at) as minute,
    COUNT(*) as events_processed
FROM user_events
WHERE processed_at > NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC;
```

### Xem Latency
```sql
SELECT 
    AVG(EXTRACT(EPOCH FROM (processed_at - event_timestamp))) as avg_latency_seconds
FROM user_events
WHERE processed_at > NOW() - INTERVAL '1 hour';
```

### Xem Table Size
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('user_events')) as total_size,
    pg_size_pretty(pg_relation_size('user_events')) as table_size,
    pg_size_pretty(pg_indexes_size('user_events')) as indexes_size;
```

---

## 🎯 Common Tasks

### Xóa Dữ Liệu Cũ
```sql
-- Xóa events cũ hơn 30 ngày
DELETE FROM user_events 
WHERE event_timestamp < NOW() - INTERVAL '30 days';
```

### Backup Table
```bash
pg_dump -U postgres -d your_db -t user_events > user_events_backup.sql
```

### Restore Table
```bash
psql -U postgres -d your_db < user_events_backup.sql
```

### Export to CSV
```sql
COPY (SELECT * FROM user_events) TO '/tmp/user_events.csv' CSV HEADER;
```

---

## 🔧 Configuration

### Thay Đổi Checkpoint Location
```python
.option("checkpointLocation", "/your/custom/path")
```

### Thay Đổi Starting Offset
```python
.option("startingOffsets", "earliest")  # Đọc từ đầu
.option("startingOffsets", "latest")    # Chỉ đọc mới
```

### Thay Đổi Batch Interval
```python
spark.conf.set("spark.sql.streaming.trigger.processingTime", "10 seconds")
```

---

## 📞 Quick Help

### Files
- `processor.py` - Code chính
- `run_user_events_subscriber.py` - Script chạy
- `setup_user_events_table.sql` - Database setup
- `README_USER_EVENTS.md` - Documentation đầy đủ
- `ARCHITECTURE.md` - Sơ đồ kiến trúc
- `SUMMARY.md` - Tóm tắt công việc

### Environment Variables
- `KAFKA_BROKER` - Kafka server address
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_HOST` - Database host
- `POSTGRES_DB` - Database name

### Key Concepts
- **Streaming**: Xử lý dữ liệu liên tục
- **Micro-batch**: Xử lý theo batch nhỏ
- **Checkpoint**: Lưu trạng thái để recovery
- **foreachBatch**: Xử lý từng batch
- **Fault Tolerance**: Khả năng chịu lỗi

---

## 💡 Tips

1. **Performance**: Tăng số partitions trong Kafka để scale
2. **Monitoring**: Theo dõi lag và processing time
3. **Cleanup**: Xóa checkpoint cũ khi thay đổi schema
4. **Testing**: Test với ít data trước khi production
5. **Backup**: Backup checkpoint và database thường xuyên

---

**Cần thêm trợ giúp? Xem `README_USER_EVENTS.md`**
