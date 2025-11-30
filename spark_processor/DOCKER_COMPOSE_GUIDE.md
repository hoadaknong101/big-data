# Hướng Dẫn Sử Dụng Docker Compose - Spark Processor

## 📋 Tổng Quan

Docker Compose đã được cấu hình với **2 services** cho Spark Processor:

1. **`spark-processor-ratings`** - Xử lý ratings (code gốc)
2. **`spark-processor-user-events`** - Subscribe user-events (code mới)

Cả hai services đều sử dụng cùng một Docker image nhưng chạy các chức năng khác nhau thông qua biến môi trường `RUN_MODE`.

---

## 🚀 Cách Sử Dụng

### Option 1: Chạy Cả Hai Services (Recommended)

```bash
# Build và start tất cả services
docker-compose up -d

# Hoặc chỉ start spark processors
docker-compose up -d spark-processor-ratings spark-processor-user-events
```

Cả hai processors sẽ chạy song song:
- `spark-processor-ratings`: Lưu click events vào bảng `ratings`
- `spark-processor-user-events`: Lưu TẤT CẢ events vào bảng `user_events`

### Option 2: Chỉ Chạy User Events Subscriber

```bash
# Chỉ start user events processor
docker-compose up -d spark-processor-user-events
```

### Option 3: Chỉ Chạy Ratings Processor (Original)

```bash
# Chỉ start ratings processor
docker-compose up -d spark-processor-ratings
```

---

## 🔧 Cấu Hình Chi Tiết

### Service: spark-processor-ratings

```yaml
spark-processor-ratings:
  build: ./spark_processor
  container_name: spark-processor-ratings
  environment:
    - RUN_MODE=ratings  # Chạy hàm main()
```

**Chức năng:**
- Subscribe topic được cấu hình trong `KAFKA_TOPIC` (.env)
- Filter chỉ lấy events có `event_type="click"`
- Lưu vào bảng `ratings` với cột: `user_id`, `movie_id`, `rating`, `timestamp`

### Service: spark-processor-user-events

```yaml
spark-processor-user-events:
  build: ./spark_processor
  container_name: spark-processor-user-events
  environment:
    - RUN_MODE=user_events  # Chạy hàm subscribe_user_events()
```

**Chức năng:**
- Subscribe topic `user-events` (hard-coded)
- Lưu TẤT CẢ events (không filter)
- Lưu vào bảng `user_events` với cột: `user_id`, `movie_id`, `event_type`, `event_timestamp`, `processed_at`

---

## 📊 So Sánh Hai Services

| Tính năng | spark-processor-ratings | spark-processor-user-events |
|-----------|------------------------|----------------------------|
| **Hàm chạy** | `main()` | `subscribe_user_events()` |
| **RUN_MODE** | `ratings` | `user_events` |
| **Topic** | `$KAFKA_TOPIC` (từ .env) | `user-events` (fixed) |
| **Filter** | Chỉ `event_type="click"` | Không filter (lưu tất cả) |
| **Target Table** | `ratings` | `user_events` |
| **Columns** | user_id, movie_id, rating, timestamp | user_id, movie_id, event_type, event_timestamp, processed_at |
| **Checkpoint** | `/tmp/checkpoint/ratings` | `/tmp/checkpoint/user-events` |

---

## 🔍 Monitoring & Logs

### Xem Logs Real-time

```bash
# Xem logs của ratings processor
docker-compose logs -f spark-processor-ratings

# Xem logs của user events processor
docker-compose logs -f spark-processor-user-events

# Xem logs của cả hai
docker-compose logs -f spark-processor-ratings spark-processor-user-events
```

### Kiểm Tra Status

```bash
# Xem status của tất cả services
docker-compose ps

# Xem chi tiết một service
docker inspect spark-processor-user-events
```

---

## 🛠️ Troubleshooting

### Rebuild Image Sau Khi Sửa Code

```bash
# Rebuild image
docker-compose build spark-processor-ratings spark-processor-user-events

# Hoặc rebuild và restart
docker-compose up -d --build spark-processor-user-events
```

### Restart Services

```bash
# Restart user events processor
docker-compose restart spark-processor-user-events

# Restart cả hai
docker-compose restart spark-processor-ratings spark-processor-user-events
```

### Stop Services

```bash
# Stop user events processor
docker-compose stop spark-processor-user-events

# Stop cả hai
docker-compose stop spark-processor-ratings spark-processor-user-events
```

### Xóa và Tạo Lại

```bash
# Xóa containers
docker-compose down

# Xóa cả volumes (CẢNH BÁO: Mất dữ liệu!)
docker-compose down -v

# Tạo lại từ đầu
docker-compose up -d --build
```

---

## 🧪 Testing

### Test User Events Processor

```bash
# 1. Start service
docker-compose up -d spark-processor-user-events

# 2. Xem logs
docker-compose logs -f spark-processor-user-events

# 3. Gửi test message vào Kafka
docker exec -it kafka kafka-console-producer --topic user-events --bootstrap-server localhost:9092
# Nhập: {"user_id":123,"movie_id":456,"event_type":"click","timestamp":1701234567890}

# 4. Kiểm tra database
docker exec -it postgres-db psql -U postgres -d your_db -c "SELECT * FROM user_events ORDER BY processed_at DESC LIMIT 5;"
```

---

## ⚙️ Environment Variables

Các biến môi trường cần thiết trong file `.env`:

```bash
# Kafka Configuration
KAFKA_BROKER=kafka:9092
KAFKA_TOPIC=your-topic  # Chỉ dùng cho ratings processor

# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres-db
POSTGRES_DB=your_database
```

**Lưu ý:**
- `KAFKA_TOPIC` chỉ ảnh hưởng đến `spark-processor-ratings`
- `spark-processor-user-events` luôn subscribe topic `user-events`

---

## 📝 Cấu Trúc Docker Compose

```
services:
  ├── postgres-db          # Database
  ├── kafka                # Message broker
  ├── spark-master         # Spark master node
  ├── spark-worker         # Spark worker node
  ├── spark-processor-ratings        # ← Ratings processor (original)
  └── spark-processor-user-events    # ← User events subscriber (new)
```

---

## 🎯 Use Cases

### Use Case 1: Development
Chạy cả hai để test song song:
```bash
docker-compose up -d spark-processor-ratings spark-processor-user-events
```

### Use Case 2: Production - Chỉ User Events
Nếu chỉ cần user events:
```bash
docker-compose up -d spark-processor-user-events
```

### Use Case 3: Migration
Chạy ratings processor trước, sau đó thêm user events:
```bash
# Bước 1
docker-compose up -d spark-processor-ratings

# Bước 2 (sau khi test OK)
docker-compose up -d spark-processor-user-events
```

---

## 🔄 Workflow Hoàn Chỉnh

```bash
# 1. Setup database
docker-compose up -d postgres-db
docker exec -it postgres-db psql -U postgres -d your_db -f /path/to/setup_user_events_table.sql

# 2. Start Kafka
docker-compose up -d kafka

# 3. Start Spark cluster
docker-compose up -d spark-master spark-worker

# 4. Start processors
docker-compose up -d spark-processor-ratings spark-processor-user-events

# 5. Monitor
docker-compose logs -f spark-processor-user-events

# 6. Test
# Gửi message vào Kafka và kiểm tra database
```

---

## 💡 Tips

1. **Separate Checkpoints**: Mỗi processor có checkpoint riêng để tránh conflict
2. **Different Container Names**: Dễ dàng identify trong logs
3. **Same Image**: Tiết kiệm disk space, chỉ build một lần
4. **Environment Variable**: Dễ dàng switch giữa các modes
5. **Independent Scaling**: Có thể scale từng processor riêng biệt

---

## 📞 Quick Commands Reference

```bash
# Start all
docker-compose up -d

# Start specific service
docker-compose up -d spark-processor-user-events

# View logs
docker-compose logs -f spark-processor-user-events

# Restart
docker-compose restart spark-processor-user-events

# Stop
docker-compose stop spark-processor-user-events

# Rebuild
docker-compose build spark-processor-user-events

# Remove
docker-compose down
```

---

**Hoàn thành! Bạn đã có 2 Spark processors chạy song song trong Docker Compose.** 🎉
