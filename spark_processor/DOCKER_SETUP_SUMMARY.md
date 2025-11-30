# ✅ Cấu Hình Docker Compose Hoàn Tất

## 🎯 Tóm Tắt

Đã cấu hình **2 Spark Processor services** trong `docker-compose.yml`:

### 1. spark-processor-ratings (Original)
- **RUN_MODE**: `ratings`
- **Topic**: `$KAFKA_TOPIC` (từ .env)
- **Filter**: Chỉ `event_type="click"`
- **Table**: `ratings`

### 2. spark-processor-user-events (New) ⭐
- **RUN_MODE**: `user_events`
- **Topic**: `user-events` (fixed)
- **Filter**: Không (lưu tất cả)
- **Table**: `user_events`

---

## 🚀 Quick Start

```bash
# Chạy cả hai processors
docker-compose up -d spark-processor-ratings spark-processor-user-events

# Hoặc chỉ user events
docker-compose up -d spark-processor-user-events

# Xem logs
docker-compose logs -f spark-processor-user-events
```

---

## 📁 Files Đã Cập Nhật

1. **`docker-compose.yml`**
   - Thêm service `spark-processor-user-events`
   - Rename service cũ thành `spark-processor-ratings`
   - Cấu hình `RUN_MODE` environment variable

2. **`spark_processor/Dockerfile`**
   - Copy thêm `run_user_events_subscriber.py`

3. **`spark_processor/processor.py`**
   - Thêm logic check `RUN_MODE` environment variable
   - Tự động chọn hàm `main()` hoặc `subscribe_user_events()`

---

## 🔧 Cách Hoạt Động

```python
# Trong processor.py
if __name__ == "__main__":
    run_mode = os.environ.get('RUN_MODE', 'ratings')
    
    if run_mode == 'user_events':
        subscribe_user_events()  # Hàm mới
    else:
        main()  # Hàm gốc
```

Docker Compose set `RUN_MODE` khác nhau cho mỗi service:
- `spark-processor-ratings`: `RUN_MODE=ratings`
- `spark-processor-user-events`: `RUN_MODE=user_events`

---

## ✅ Checklist

- [x] Cập nhật `docker-compose.yml` với 2 services
- [x] Cập nhật `Dockerfile` để copy cả 2 scripts
- [x] Cập nhật `processor.py` với RUN_MODE logic
- [x] Tạo documentation (`DOCKER_COMPOSE_GUIDE.md`)
- [x] Test configuration

---

## 📖 Documentation

Xem chi tiết tại: [`DOCKER_COMPOSE_GUIDE.md`](DOCKER_COMPOSE_GUIDE.md)

---

**Ready to use!** 🎉
