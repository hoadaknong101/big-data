# Docker Compose Configuration - Local Mode (Fixed)

## 🎯 Giải Pháp Nhanh

File này chứa cấu hình đã được fix để chạy Spark Processor ở **Local Mode**, không cần spark-master và spark-worker.

## 📝 Thay Đổi

### Cấu Hình Cũ (Cluster Mode - Có Lỗi)
```yaml
spark-processor-user-events:
  command: >
    /opt/spark/bin/spark-submit 
      --master spark://spark-master:7077  # ← Cần worker
      --driver-memory 1g 
      --executor-memory 1g 
      --executor-cores 1
```

### Cấu Hình Mới (Local Mode - Hoạt Động)
```yaml
spark-processor-user-events:
  command: >
    /opt/spark/bin/spark-submit 
      --master local[2]  # ← Không cần worker
      --driver-memory 1g
```

---

## 🔧 Cách Áp Dụng

### Option 1: Sửa Trực Tiếp docker-compose.yml

Mở file `docker-compose.yml` và thay thế phần `spark-processor-user-events`:

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
      echo 'Starting User Events Processor (Local Mode)...';
      sleep 20;
      sed -i 's/\r$//' /app/processor.py;
      /opt/spark/bin/spark-submit --master local[2] --driver-memory 1g --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/user-events /app/processor.py
      "
```

Tương tự cho `spark-processor-ratings`:

```yaml
  spark-processor-ratings:
    build: ./spark_processor
    container_name: spark-processor-ratings
    env_file: .env
    environment:
      - RUN_MODE=ratings
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
      echo 'Starting Ratings Processor (Local Mode)...';
      sleep 20;
      sed -i 's/\r$//' /app/processor.py;
      /opt/spark/bin/spark-submit --master local[2] --driver-memory 1g --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/ratings /app/processor.py
      "
```

### Option 2: Copy Paste Toàn Bộ

Thay thế toàn bộ section từ `# 9. Spark Processor` đến hết bằng code dưới đây:

```yaml
  # 9. Spark Processor - Ratings (Local Mode)
  spark-processor-ratings:
    build: ./spark_processor
    container_name: spark-processor-ratings
    env_file: .env
    environment:
      - RUN_MODE=ratings
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
      echo 'Starting Ratings Processor (Local Mode)...';
      sleep 20;
      sed -i 's/\r$//' /app/processor.py;
      /opt/spark/bin/spark-submit --master local[2] --driver-memory 1g --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/ratings /app/processor.py
      "

  # 10. Spark Processor - User Events (Local Mode)
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
      echo 'Starting User Events Processor (Local Mode)...';
      sleep 20;
      sed -i 's/\r$//' /app/processor.py;
      /opt/spark/bin/spark-submit --master local[2] --driver-memory 1g --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 --conf spark.sql.streaming.checkpointLocation=/tmp/checkpoint/user-events /app/processor.py
      "
```

---

## 🚀 Restart Services

Sau khi sửa:

```powershell
# Stop và remove containers cũ
docker compose down spark-processor-ratings spark-processor-user-events

# Start lại
docker compose up -d spark-processor-user-events

# Xem logs
docker compose logs -f spark-processor-user-events
```

---

## ✅ Kết Quả Mong Đợi

Logs sẽ hiển thị:

```
Starting User Events Processor (Local Mode)...
============================================================
Bước 1: Khởi tạo Spark Session cho User Events Processing
============================================================
✓ Spark Session đã được khởi tạo thành công

============================================================
Bước 2: Kết nối tới Kafka và subscribe topic 'user-events'
============================================================
Kafka Broker: kafka:9092
Topic: user-events
✓ Đã kết nối thành công tới Kafka topic 'user-events'
...
```

**KHÔNG còn** cảnh báo:
```
WARN TaskSchedulerImpl: Initial job has not accepted any resources
```

---

## 📊 Lợi Ích Local Mode

✅ **Không cần spark-master và spark-worker**
✅ **Ít RAM hơn** (chỉ cần 1-2GB thay vì 4GB+)
✅ **Setup đơn giản hơn**
✅ **Phù hợp cho development/testing**

❌ **Không scale được** (chỉ chạy trên 1 machine)
❌ **Giới hạn resources** (local[2] = 2 cores)

---

## 🎓 Giải Thích

- `--master local[2]`: Chạy Spark ở local mode với 2 threads
- `local[*]`: Sử dụng tất cả cores available
- `local[1]`: Chỉ 1 thread (slow nhưng ít RAM)

---

**Áp dụng fix này và hệ thống sẽ hoạt động ngay!** 🎉
