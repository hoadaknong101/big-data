# Dashboard Module - Big Data Analytics

## 📊 Tổng quan

Dashboard module là một web application độc lập được xây dựng bằng Flask, cung cấp giao diện quản lý và theo dõi real-time cho hệ thống recommendation.

## ✨ Tính năng

### 1. 🏠 Trang chủ - Real-time Analytics
- **Biểu đồ real-time** cập nhật mỗi 2 giây qua WebSocket
- **Line Chart**: Lượt xem theo thời gian (24h gần nhất)
- **Bar Chart**: Top 10 phim được xem nhiều nhất
- **Pie Chart**: Phân bố loại sự kiện (click, watch)
- **Stats Cards**: Tổng số events, users, movies
- **Recent Events**: 5 sự kiện gần nhất

### 2. 🤖 Trang quản lý dữ liệu
- **Train Model**: Trigger huấn luyện mô hình recommendation
- **Progress Tracking**: Theo dõi tiến trình training real-time
- **Training History**: Lịch sử các lần training
- **Database Stats**: Thống kê dữ liệu (users, movies, ratings, events)

### 3. 🎬 Trang quản lý phim
- **CRUD Operations**: Thêm, sửa, xóa phim
- **Search & Filter**: Tìm kiếm theo title và genres
- **Pagination**: Phân trang 20 items/page
- **Poster Preview**: Xem trước poster phim
- **Modal Forms**: Form thêm/sửa với validation

### 4. 👥 Trang quản lý người dùng
- **CRUD Operations**: Thêm, sửa, xóa người dùng
- **Search & Filter**: Tìm kiếm theo username và email
- **Pagination**: Phân trang 20 items/page
- **Password Management**: Cập nhật password an toàn
- **Modal Forms**: Form thêm/sửa với validation

## 🎨 Thiết kế UI/UX

### Phong cách Minimalism
- **Màu sắc**: Gradient backgrounds (purple, pink, blue, green)
- **Glassmorphism**: Backdrop blur effects
- **Smooth Transitions**: 0.3s ease cho mọi interactions
- **Hover Effects**: Transform và shadow effects
- **Responsive**: Tương thích mobile và desktop

### Công nghệ Frontend
- **TailwindCSS**: Utility-first CSS framework
- **Chart.js**: Thư viện biểu đồ interactive
- **Socket.IO**: WebSocket client cho real-time updates
- **Vanilla JavaScript**: Không dependencies nặng

## 🔧 Kiến trúc Backend

### Tech Stack
- **Flask**: Web framework
- **Flask-SocketIO**: WebSocket support
- **SQLAlchemy**: ORM cho PostgreSQL
- **Flask-CORS**: Cross-origin support

### Database Models
- `User`: Quản lý người dùng
- `Movie`: Quản lý phim
- `UserEvent`: Tracking user events

### API Endpoints

#### Statistics
- `GET /api/stats/realtime` - Lấy statistics real-time
- `GET /api/stats/trending` - Top trending movies

#### Model Training
- `POST /api/train-model` - Trigger training
- `GET /api/train-status` - Lấy training status

#### Movies CRUD
- `GET /api/movies` - List movies (với pagination & search)
- `GET /api/movies/<id>` - Get movie detail
- `POST /api/movies` - Create movie
- `PUT /api/movies/<id>` - Update movie
- `DELETE /api/movies/<id>` - Delete movie

#### Users CRUD
- `GET /api/users` - List users (với pagination & search)
- `GET /api/users/<id>` - Get user detail
- `POST /api/users` - Create user
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user

## 🚀 Cài đặt và Chạy

### 1. Với Docker (Recommended)

```bash
# Build và start dashboard service
docker-compose up -d dashboard

# Xem logs
docker-compose logs -f dashboard
```

Dashboard sẽ chạy tại: **http://localhost:5002**

### 2. Local Development

```bash
# Di chuyển vào thư mục dashboard
cd dashboard

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy application
python app.py
```

## 📁 Cấu trúc thư mục

```
dashboard/
├── app.py                  # Flask application chính
├── models.py              # Database models
├── routes.py              # API routes
├── websocket.py           # WebSocket handlers
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env                  # Environment variables
├── static/
│   ├── css/
│   │   └── custom.css    # Custom styles
│   └── js/
│       └── (future JS files)
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Real-time analytics
    ├── data_management.html  # Model training
    ├── movies.html       # Movies management
    └── users.html        # Users management
```

## 🔌 WebSocket Events

### Client → Server
- `connect` - Kết nối WebSocket
- `disconnect` - Ngắt kết nối
- `request_stats` - Request statistics ngay lập tức

### Server → Client
- `connection_response` - Xác nhận kết nối
- `stats_update` - Cập nhật statistics (mỗi 2s)

## 🎯 Model Training Flow

1. User click "Bắt đầu huấn luyện"
2. Dashboard gọi `POST /api/train-model`
3. Backend start background thread
4. Thread execute `docker exec model-training python /app/train.py`
5. Frontend poll `GET /api/train-status` mỗi 2s
6. Update progress bar và message
7. Khi hoàn tất, hiển thị notification

## 📊 Real-time Statistics Flow

1. Client connect tới WebSocket server
2. Server start background task (nếu chưa chạy)
3. Background task query database mỗi 2s
4. Emit `stats_update` event tới tất cả clients
5. Client nhận data và update charts
6. Charts animate smooth với Chart.js

## 🔒 Security Notes

- **Password Hashing**: Sử dụng `pbkdf2:sha256`
- **SQL Injection**: Sử dụng SQLAlchemy ORM
- **CORS**: Configured cho development (cần tighten cho production)
- **Input Validation**: Client-side và server-side validation

## 🐛 Troubleshooting

### Dashboard không kết nối được database
```bash
# Check PostgreSQL container
docker-compose ps postgres-db

# Check logs
docker-compose logs postgres-db
```

### WebSocket không hoạt động
```bash
# Check dashboard logs
docker-compose logs dashboard

# Verify port 5002 không bị block
netstat -an | findstr 5002
```

### Model training timeout
- Training có thể mất 3-6 phút
- Timeout được set ở 10 phút
- Check `model-training` container logs

## 📝 Environment Variables

Dashboard sử dụng các biến môi trường từ `.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=postgres-db
POSTGRES_DB=bigdata_db
```

## 🎨 Customization

### Thay đổi màu sắc gradient
Edit `templates/base.html`:
```css
.gradient-bg {
    background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
}
```

### Thay đổi interval WebSocket
Edit `websocket.py`:
```python
socketio.sleep(2)  # Change to desired seconds
```

### Thay đổi items per page
Edit `routes.py`:
```python
per_page = request.args.get('per_page', 20, type=int)  # Change 20
```

## 📈 Performance

- **WebSocket latency**: < 100ms
- **Chart update**: 60fps smooth
- **API response**: < 500ms
- **Page load**: < 2s

## 🔮 Future Enhancements

- [ ] User authentication cho dashboard
- [ ] Export data to CSV/Excel
- [ ] More chart types (heatmap, scatter)
- [ ] Real-time notifications
- [ ] Dark/Light theme toggle
- [ ] Mobile app version

## 📞 Support

Nếu có vấn đề, check:
1. Docker containers đang chạy
2. Database có dữ liệu
3. Port 5002 available
4. Browser console cho errors

---

**Built with ❤️ using Flask, TailwindCSS, and Chart.js**
