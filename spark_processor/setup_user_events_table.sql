-- ============================================================
-- Script tạo bảng user_events cho Spark Streaming Processor
-- ============================================================
-- Mục đích: Lưu trữ tất cả events từ Kafka topic 'user-events'
-- Sử dụng: Chạy script này trong PostgreSQL trước khi chạy
--          hàm subscribe_user_events()
-- ============================================================

-- Bước 1: Xóa bảng cũ nếu tồn tại (Cẩn thận: sẽ mất dữ liệu!)
-- Uncomment dòng dưới nếu muốn tạo lại bảng từ đầu
-- DROP TABLE IF EXISTS user_events;

-- Bước 2: Tạo bảng user_events
CREATE TABLE IF NOT EXISTS user_events (
    -- Primary key tự động tăng
    id SERIAL PRIMARY KEY,
    
    -- Thông tin từ Kafka message
    user_id INTEGER NOT NULL,           -- ID người dùng
    movie_id INTEGER NOT NULL,          -- ID phim
    event_type VARCHAR(50) NOT NULL,    -- Loại sự kiện (click, watch, etc.)
    
    -- Thông tin thời gian
    event_timestamp TIMESTAMP NOT NULL,  -- Thời gian sự kiện xảy ra (từ Kafka)
    processed_at TIMESTAMP NOT NULL,     -- Thời gian xử lý bởi Spark
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Thời gian insert vào DB
);

-- Bước 3: Tạo các index để tăng tốc độ truy vấn
-- Index trên user_id (để query theo user)
CREATE INDEX IF NOT EXISTS idx_user_events_user_id 
ON user_events(user_id);

-- Index trên movie_id (để query theo phim)
CREATE INDEX IF NOT EXISTS idx_user_events_movie_id 
ON user_events(movie_id);

-- Index trên event_type (để filter theo loại event)
CREATE INDEX IF NOT EXISTS idx_user_events_event_type 
ON user_events(event_type);

-- Index trên event_timestamp (để query theo thời gian)
CREATE INDEX IF NOT EXISTS idx_user_events_timestamp ON user_events(event_timestamp DESC);

-- Composite index cho các query phổ biến
CREATE INDEX IF NOT EXISTS idx_user_events_user_movie ON user_events(user_id, movie_id);

CREATE INDEX IF NOT EXISTS idx_user_events_user_type ON user_events(user_id, event_type);

-- Bước 4: Tạo view để xem thống kê nhanh
CREATE OR REPLACE VIEW user_events_stats AS
SELECT 
    event_type,
    COUNT(*) as total_events,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT movie_id) as unique_movies,
    MIN(event_timestamp) as first_event,
    MAX(event_timestamp) as last_event
FROM user_events
GROUP BY event_type;

-- Bước 5: Tạo function để xem events gần nhất
CREATE OR REPLACE FUNCTION get_recent_events(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    id INTEGER,
    user_id INTEGER,
    movie_id INTEGER,
    event_type VARCHAR,
    event_timestamp TIMESTAMP,
    processed_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ue.id,
        ue.user_id,
        ue.movie_id,
        ue.event_type,
        ue.event_timestamp,
        ue.processed_at
    FROM user_events ue
    ORDER BY ue.processed_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Bước 6: Tạo function để xem events của một user
CREATE OR REPLACE FUNCTION get_user_events(p_user_id INTEGER, limit_count INTEGER DEFAULT 100)
RETURNS TABLE (
    id INTEGER,
    movie_id INTEGER,
    event_type VARCHAR,
    event_timestamp TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ue.id,
        ue.movie_id,
        ue.event_type,
        ue.event_timestamp
    FROM user_events ue
    WHERE ue.user_id = p_user_id
    ORDER BY ue.event_timestamp DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Các câu query hữu ích để kiểm tra dữ liệu
-- ============================================================

-- Xem cấu trúc bảng
-- \d user_events

-- Xem tổng số events
-- SELECT COUNT(*) FROM user_events;

-- Xem thống kê theo event_type
-- SELECT * FROM user_events_stats;

-- Xem 10 events mới nhất
-- SELECT * FROM get_recent_events(10);

-- Xem events của user 123
-- SELECT * FROM get_user_events(123, 50);

-- Xem events trong 1 giờ qua
-- SELECT * FROM user_events 
-- WHERE event_timestamp > NOW() - INTERVAL '1 hour'
-- ORDER BY event_timestamp DESC;

-- Xem top 10 users có nhiều events nhất
-- SELECT user_id, COUNT(*) as event_count
-- FROM user_events
-- GROUP BY user_id
-- ORDER BY event_count DESC
-- LIMIT 10;

-- Xem top 10 movies được tương tác nhiều nhất
-- SELECT movie_id, COUNT(*) as interaction_count
-- FROM user_events
-- GROUP BY movie_id
-- ORDER BY interaction_count DESC
-- LIMIT 10;

-- ============================================================
-- Hoàn thành! Bảng user_events đã sẵn sàng sử dụng
-- ============================================================
