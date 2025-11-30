# 🔧 Troubleshooting: Spark Worker Connection Issue

## ❌ Vấn Đề

Logs hiển thị cảnh báo:
```
WARN TaskSchedulerImpl: Initial job has not accepted any resources; 
check your cluster UI to ensure that workers are registered and have sufficient resources
```

## 🔍 Nguyên Nhân

Có 3 nguyên nhân chính:

### 1. Spark Worker Chưa Đăng Ký với Master
- Worker container chạy nhưng không kết nối được với Master
- Network issues
- Master URL không đúng

### 2. Worker Không Đủ Tài Nguyên
- Memory/CPU được cấu hình quá cao
- Host machine không đủ resources

### 3. Timing Issue
- Processor start quá sớm, trước khi Worker ready
- Sleep 40s có thể chưa đủ

---

## ✅ Cách Kiểm Tra

### Bước 1: Kiểm Tra Status Containers

```powershell
# Xem tất cả containers
docker ps -a

# Hoặc với Docker Compose
docker compose ps
```

**Kiểm tra:**
- `spark-master` - Status phải là `Up`
- `spark-worker` - Status phải là `Up`
- `spark-processor-*` - Có thể `Restarting` nếu lỗi

### Bước 2: Xem Logs Spark Master

```powershell
docker logs spark-master --tail=100
```

**Tìm kiếm:**
- `Registering worker` - Worker đã đăng ký thành công
- Nếu KHÔNG thấy → Worker chưa kết nối

### Bước 3: Xem Logs Spark Worker

```powershell
docker logs spark-worker --tail=100
```

**Tìm kiếm:**
- `Successfully registered with master` - Kết nối OK
- `Failed to connect` hoặc `Connection refused` - Lỗi kết nối

### Bước 4: Kiểm Tra Spark UI

Mở browser và truy cập:
```
http://localhost:8082
```

**Kiểm tra:**
- **Workers** tab: Phải có ít nhất 1 worker
- **Cores**: Số cores available > 0
- **Memory**: Memory available > 0

Nếu không có worker nào → Worker chưa đăng ký!

---

## 🔧 Giải Pháp

### Giải Pháp 1: Tăng Sleep Time

Nếu Worker cần nhiều thời gian hơn để start:

**File**: `docker-compose.yml`

```yaml
spark-processor-user-events:
  command: >
    /bin/bash -c "
    echo 'Waiting for Spark cluster to be ready...';
    sleep 60;  # ← Tăng từ 40 lên 60 giây
    ...
```

### Giải Pháp 2: Giảm Resource Requirements

Nếu Worker không đủ resources:

**File**: `docker-compose.yml`

```yaml
spark-worker:
  environment:
    - SPARK_WORKER_CORES=1      # ← Giảm từ 2 xuống 1
    - SPARK_WORKER_MEMORY=1G    # ← Giảm từ 2G xuống 1G
```

Và trong processor command:

```yaml
spark-processor-user-events:
  command: >
    /bin/bash -c "
    ...
    /opt/spark/bin/spark-submit 
      --driver-memory 512m      # ← Giảm từ 1g xuống 512m
      --executor-memory 512m    # ← Giảm từ 1g xuống 512m
      --executor-cores 1 
      ...
```

### Giải Pháp 3: Sử Dụng Local Mode (Không Cần Worker)

Nếu vẫn không được, chạy Spark ở local mode:

**File**: `docker-compose.yml`

```yaml
spark-processor-user-events:
  command: >
    /bin/bash -c "
    echo 'Waiting for dependencies...';
    sleep 20;
    sed -i 's/\r$//' /app/processor.py;
    /opt/spark/bin/spark-submit 
      --master local[2]  # ← Thay vì spark://spark-master:7077
      --driver-memory 1g 
      --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 
      --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/user-events 
      /app/processor.py
    "
```

**Lưu ý**: Local mode không cần spark-master và spark-worker!

### Giải Pháp 4: Thêm Health Check Dependency

Đảm bảo processor chỉ start khi worker đã ready:

**File**: `docker-compose.yml`

Thêm healthcheck cho spark-worker:

```yaml
spark-worker:
  # ... existing config ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8081"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
```

Và update dependency:

```yaml
spark-processor-user-events:
  depends_on:
    spark-worker:
      condition: service_healthy  # ← Thay vì service_started
```

---

## 📋 Checklist Troubleshooting

Hãy làm theo thứ tự:

- [ ] 1. Kiểm tra `docker ps` - Tất cả containers đang chạy?
- [ ] 2. Xem `docker logs spark-master` - Worker đã register?
- [ ] 3. Xem `docker logs spark-worker` - Có lỗi connection?
- [ ] 4. Mở `http://localhost:8082` - Có worker trong UI?
- [ ] 5. Nếu không có worker → Restart worker: `docker restart spark-worker`
- [ ] 6. Nếu vẫn lỗi → Áp dụng Giải pháp 1 (tăng sleep time)
- [ ] 7. Nếu vẫn lỗi → Áp dụng Giải pháp 2 (giảm resources)
- [ ] 8. Nếu vẫn lỗi → Áp dụng Giải pháp 3 (local mode)

---

## 🚀 Quick Fix (Recommended)

**Cách nhanh nhất**: Sử dụng Local Mode

1. **Sửa docker-compose.yml**:

```yaml
spark-processor-user-events:
  build: ./spark_processor
  container_name: spark-processor-user-events
  env_file: .env
  environment:
    - RUN_MODE=user_events
  networks:
    - app-network
  depends_on:
    kafka:
      condition: service_healthy
    postgres-db:
      condition: service_healthy
  restart: on-failure
  command: >
    /bin/bash -c "
    echo 'Starting User Events Processor...';
    sleep 20;
    sed -i 's/\r$//' /app/processor.py;
    /opt/spark/bin/spark-submit --master local[2] --driver-memory 1g --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/user-events /app/processor.py
    "
```

2. **Restart**:

```powershell
docker compose down spark-processor-user-events
docker compose up -d spark-processor-user-events
docker compose logs -f spark-processor-user-events
```

---

## 📊 So Sánh Modes

| Feature | Cluster Mode | Local Mode |
|---------|--------------|------------|
| **Master** | spark://spark-master:7077 | local[2] |
| **Workers** | Cần spark-worker | Không cần |
| **Scalability** | Có thể scale | Không scale được |
| **Setup** | Phức tạp hơn | Đơn giản |
| **Resources** | Cần nhiều RAM | Ít RAM hơn |
| **Use Case** | Production, big data | Development, testing |

**Khuyến nghị**: 
- Development/Testing → Dùng **Local Mode**
- Production → Dùng **Cluster Mode** (cần fix worker issue)

---

## 💡 Tips

1. **Kiểm tra RAM**: Đảm bảo máy có ít nhất 4GB RAM free
2. **Docker Resources**: Trong Docker Desktop → Settings → Resources → Tăng Memory lên 4GB+
3. **Logs**: Luôn check logs của cả 3: master, worker, processor
4. **UI**: Spark UI rất hữu ích để debug

---

## 🎯 Next Steps

Sau khi fix:

```powershell
# 1. Restart services
docker compose restart spark-processor-user-events

# 2. Xem logs
docker compose logs -f spark-processor-user-events

# 3. Test với message
docker exec -it kafka kafka-console-producer --topic user-events --bootstrap-server localhost:9092
# Input: {"user_id":123,"movie_id":456,"event_type":"click","timestamp":1701234567890}

# 4. Kiểm tra database
docker exec -it postgres-db psql -U postgres -d your_db -c "SELECT * FROM user_events LIMIT 5;"
```

---

**Hãy thử các bước trên và cho tôi biết kết quả!** 🚀
