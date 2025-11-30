"""
Example script để chạy hàm subscribe_user_events()

Script này demo cách sử dụng hàm subscribe_user_events() để
subscribe topic 'user-events' và lưu dữ liệu real-time vào PostgreSQL.

Cách chạy:
    python run_user_events_subscriber.py

Yêu cầu:
    1. Kafka đang chạy và có topic 'user-events'
    2. PostgreSQL đang chạy và đã tạo bảng 'user_events'
    3. Các biến môi trường đã được set đúng
"""

import os
import sys

# Import hàm subscribe_user_events từ processor.py
from processor import subscribe_user_events

def check_environment():
    """
    Kiểm tra các biến môi trường cần thiết
    """
    print("=" * 60)
    print("Kiểm tra Environment Variables")
    print("=" * 60)
    
    required_vars = [
        'KAFKA_BROKER',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_HOST',
        'POSTGRES_DB'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Ẩn password khi hiển thị
            if 'PASSWORD' in var:
                print(f"✓ {var}: {'*' * len(value)}")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: MISSING")
            missing_vars.append(var)
    
    print()
    
    if missing_vars:
        print("❌ Thiếu các biến môi trường sau:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nVui lòng set các biến môi trường trước khi chạy!")
        print("Ví dụ:")
        print("  export KAFKA_BROKER=localhost:9092")
        print("  export POSTGRES_USER=your_user")
        print("  export POSTGRES_PASSWORD=your_password")
        print("  export POSTGRES_HOST=localhost")
        print("  export POSTGRES_DB=your_database")
        return False
    
    print("✓ Tất cả biến môi trường đã được set!\n")
    return True

def main():
    """
    Hàm main để chạy subscriber
    """
    print("\n" + "=" * 60)
    print("USER EVENTS SUBSCRIBER - REAL-TIME KAFKA TO POSTGRESQL")
    print("=" * 60)
    print()
    
    # Kiểm tra environment variables
    if not check_environment():
        sys.exit(1)
    
    print("=" * 60)
    print("Bắt đầu Subscribe User Events")
    print("=" * 60)
    print("Topic: user-events")
    print("Mode: Real-time streaming")
    print("Target: PostgreSQL table 'user_events'")
    print()
    print("Nhấn Ctrl+C để dừng chương trình")
    print("=" * 60)
    print()
    
    try:
        # Gọi hàm subscribe_user_events
        # Hàm này sẽ chạy mãi mãi cho đến khi bị dừng
        subscribe_user_events()
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Đã nhận tín hiệu dừng từ người dùng (Ctrl+C)")
        print("Chương trình đã dừng thành công!")
        print("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        print("\n\n" + "=" * 60)
        print("❌ LỖI XẢY RA")
        print("=" * 60)
        print(f"Chi tiết lỗi: {str(e)}")
        print()
        print("Các bước khắc phục:")
        print("1. Kiểm tra Kafka đang chạy: docker ps | grep kafka")
        print("2. Kiểm tra PostgreSQL đang chạy: docker ps | grep postgres")
        print("3. Kiểm tra topic tồn tại: kafka-topics --list")
        print("4. Kiểm tra bảng user_events đã được tạo")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
