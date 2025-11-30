import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, lit, current_timestamp, when, unix_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, TimestampType

# --- Configs ---
KAFKA_BROKER = os.environ.get('KAFKA_BROKER')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('POSTGRES_HOST')
DB_NAME = os.environ.get('POSTGRES_DB')
DB_URL = f"jdbc:postgresql://{DB_HOST}:5432/{DB_NAME}"
DB_TABLE = "ratings"

# --- Hàm Subscribe User Events ---
def subscribe_user_events():
    """
    Hàm này thực hiện subscribe topic 'user-events' từ Kafka và lưu tất cả
    các message mới vào cơ sở dữ liệu PostgreSQL theo thời gian thực.
    
    Hàm sẽ chạy liên tục và đợi khi có message mới từ topic user-events.
    """
    
    # Bước 1: Khởi tạo Spark Session
    # SparkSession là điểm vào chính để làm việc với Spark
    # AppName giúp nhận diện ứng dụng trong Spark UI
    print("=" * 60)
    print("Bước 1: Khởi tạo Spark Session cho User Events Processing")
    print("=" * 60)
    
    spark = SparkSession \
        .builder \
        .appName("UserEventsSubscriber") \
        .getOrCreate()
    
    # Giảm mức độ log để dễ theo dõi, chỉ hiển thị WARNING trở lên
    spark.sparkContext.setLogLevel("WARN")
    print("✓ Spark Session đã được khởi tạo thành công\n")
    
    # Bước 2: Kết nối và đọc stream từ Kafka topic 'user-events'
    # readStream: Tạo một DataFrame streaming (dữ liệu liên tục)
    # format("kafka"): Chỉ định nguồn dữ liệu là Kafka
    print("=" * 60)
    print("Bước 2: Kết nối tới Kafka và subscribe topic 'user-events'")
    print("=" * 60)
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Topic: user-events")
    
    kafka_stream_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", "user-events") \
        .option("startingOffsets", "latest") \
        .load()
    
    # startingOffsets="latest": Chỉ đọc message mới từ thời điểm hiện tại
    # Nếu muốn đọc từ đầu, dùng "earliest"
    print("✓ Đã kết nối thành công tới Kafka topic 'user-events'\n")
    
    # Bước 3: Định nghĩa Schema cho dữ liệu JSON
    # Schema giúp Spark hiểu cấu trúc dữ liệu trong message
    # Mỗi message từ topic user-events có cấu trúc: user_id, movie_id, event_type, timestamp
    print("=" * 60)
    print("Bước 3: Định nghĩa Schema cho dữ liệu JSON")
    print("=" * 60)
    
    user_events_schema = StructType([
        StructField("user_id", IntegerType(), True),      # ID người dùng
        StructField("movie_id", IntegerType(), True),     # ID phim
        StructField("event_type", StringType(), True),    # Loại sự kiện (click, watch, etc.)
        StructField("timestamp", LongType(), True),       # Thời gian sự kiện (Unix timestamp)
    ])
    
    print("✓ Schema đã được định nghĩa:")
    print("  - user_id: IntegerType")
    print("  - movie_id: IntegerType")
    print("  - event_type: StringType")
    print("  - timestamp: LongType\n")
    
    # Bước 4: Parse dữ liệu JSON từ Kafka message
    # Kafka message có format: key, value, topic, partition, offset, timestamp
    # Chúng ta quan tâm đến 'value' - nơi chứa dữ liệu JSON
    print("=" * 60)
    print("Bước 4: Parse dữ liệu JSON từ Kafka message")
    print("=" * 60)
    
    # Chuyển đổi value từ binary sang string
    # Sau đó parse JSON theo schema đã định nghĩa
    parsed_events_df = kafka_stream_df \
        .selectExpr("CAST(value AS STRING)") \
        .withColumn("data", from_json(col("value"), user_events_schema)) \
        .select("data.*")
    
    print("✓ Dữ liệu JSON đã được parse thành công\n")
    
    # Bước 5: Chuyển đổi và làm sạch dữ liệu
    # Chuyển timestamp từ Unix timestamp (Long) sang TimestampType
    # Thêm cột processed_at để biết thời điểm xử lý
    print("=" * 60)
    print("Bước 5: Chuyển đổi và làm sạch dữ liệu")
    print("=" * 60)
    
    transformed_events_df = parsed_events_df \
        .withColumn("event_timestamp", (col("timestamp") / 1000).cast(TimestampType())) \
        .withColumn("processed_at", current_timestamp()) \
        .select(
            "user_id",
            "movie_id", 
            "event_type",
            "event_timestamp",
            "processed_at"
        )
    
    print("✓ Dữ liệu đã được chuyển đổi:")
    print("  - timestamp (ms) -> event_timestamp (TimestampType)")
    print("  - Thêm cột processed_at (thời điểm xử lý)\n")
    
    # Bước 6: Định nghĩa hàm ghi dữ liệu vào PostgreSQL
    # foreachBatch cho phép xử lý từng batch dữ liệu
    # Mỗi khi có message mới, hàm này sẽ được gọi
    print("=" * 60)
    print("Bước 6: Chuẩn bị ghi dữ liệu vào PostgreSQL")
    print("=" * 60)
    print(f"Database URL: {DB_URL}")
    print(f"Target Table: user_events\n")
    
    def write_user_events_to_postgres(batch_df, epoch_id):
        """
        Hàm này được gọi cho mỗi micro-batch của streaming data
        
        Parameters:
        - batch_df: DataFrame chứa dữ liệu của batch hiện tại
        - epoch_id: ID của batch (tăng dần theo thời gian)
        """
        
        # Kiểm tra xem batch có dữ liệu không
        record_count = batch_df.count()
        
        if record_count > 0:
            print(f"\n{'='*60}")
            print(f"Epoch {epoch_id}: Đang xử lý {record_count} records mới")
            print(f"{'='*60}")
            
            # Hiển thị một vài record mẫu để debug
            print("Sample data:")
            batch_df.show(5, truncate=False)
            
            # Ghi dữ liệu vào PostgreSQL
            # mode("append"): Thêm dữ liệu mới vào bảng, không ghi đè
            batch_df.write \
                .format("jdbc") \
                .option("url", DB_URL) \
                .option("dbtable", "user_events") \
                .option("user", DB_USER) \
                .option("password", DB_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            print(f"✓ Đã ghi thành công {record_count} records vào bảng user_events")
            print(f"{'='*60}\n")
        else:
            print(f"Epoch {epoch_id}: Không có dữ liệu mới trong batch này")
    
    # Bước 7: Bắt đầu streaming query
    # writeStream: Bắt đầu ghi streaming data
    # outputMode("append"): Chỉ ghi các row mới
    # foreachBatch: Xử lý từng batch bằng hàm đã định nghĩa
    print("=" * 60)
    print("Bước 7: Bắt đầu Streaming Query")
    print("=" * 60)
    print("Streaming đang chạy và đợi message mới từ topic 'user-events'...")
    print("Nhấn Ctrl+C để dừng\n")
    
    query = transformed_events_df \
        .writeStream \
        .outputMode("append") \
        .foreachBatch(write_user_events_to_postgres) \
        .option("checkpointLocation", "/tmp/checkpoint/user-events") \
        .start()
    
    # checkpointLocation: Lưu trạng thái xử lý để có thể recovery khi bị lỗi
    # Spark sẽ nhớ message nào đã được xử lý
    
    print("✓ Streaming Query đã được khởi động thành công!")
    print("✓ Hệ thống đang lắng nghe và xử lý message real-time...\n")
    
    # Bước 8: Chờ đợi và xử lý liên tục
    # awaitTermination(): Giữ cho chương trình chạy mãi mãi
    # Chỉ dừng khi có lỗi hoặc người dùng dừng thủ công (Ctrl+C)
    print("=" * 60)
    print("Bước 8: Chạy liên tục và đợi message mới")
    print("=" * 60)
    print("Hệ thống đang hoạt động 24/7...")
    print("Mỗi khi có message mới trong topic 'user-events',")
    print("dữ liệu sẽ tự động được lưu vào database.\n")
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Đã nhận tín hiệu dừng từ người dùng")
        print("Đang dừng Streaming Query...")
        print("=" * 60)
        query.stop()
        print("✓ Streaming Query đã dừng thành công")
    except Exception as e:
        print(f"\n\n❌ Lỗi xảy ra: {str(e)}")
        query.stop()
        raise


# --- Hàm Main (Ratings Processor) ---
def main():
    """
    Hàm main - xử lý ratings từ Kafka topic được cấu hình
    
    Hàm này subscribe topic từ biến môi trường KAFKA_TOPIC,
    filter lấy events có event_type="click" hoặc "watch",
    và lưu vào bảng ratings với rating: click=4.0, watch=5.0
    """
    
    # Bước 1: Khởi tạo Spark Session
    # SparkSession là điểm vào chính để làm việc với Spark
    # AppName giúp nhận diện ứng dụng trong Spark UI
    print("=" * 60)
    print("Bước 1: Khởi tạo Spark Session cho Ratings Processing")
    print("=" * 60)
    
    spark = SparkSession \
        .builder \
        .appName("RatingsProcessor") \
        .getOrCreate()
    
    # Giảm mức độ log để dễ theo dõi, chỉ hiển thị WARNING trở lên
    spark.sparkContext.setLogLevel("WARN")
    print("✓ Spark Session đã được khởi tạo thành công\n")
    
    # Bước 2: Kết nối và đọc stream từ Kafka topic
    # readStream: Tạo một DataFrame streaming (dữ liệu liên tục)
    # format("kafka"): Chỉ định nguồn dữ liệu là Kafka
    print("=" * 60)
    print("Bước 2: Kết nối tới Kafka và subscribe topic")
    print("=" * 60)
    print(f"Kafka Broker: {KAFKA_BROKER}")
    print(f"Topic: {KAFKA_TOPIC}")
    
    kafka_stream_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()
    
    # startingOffsets="latest": Chỉ đọc message mới từ thời điểm hiện tại
    # Nếu muốn đọc từ đầu, dùng "earliest"
    print(f"✓ Đã kết nối thành công tới Kafka topic '{KAFKA_TOPIC}'\n")
    
    # Bước 3: Định nghĩa Schema cho dữ liệu JSON
    # Schema giúp Spark hiểu cấu trúc dữ liệu trong message
    # Mỗi message có cấu trúc: user_id, movie_id, event_type, timestamp
    print("=" * 60)
    print("Bước 3: Định nghĩa Schema cho dữ liệu JSON")
    print("=" * 60)
    
    ratings_schema = StructType([
        StructField("user_id", IntegerType(), True),      # ID người dùng
        StructField("movie_id", IntegerType(), True),     # ID phim
        StructField("event_type", StringType(), True),    # Loại sự kiện (click, watch, etc.)
        StructField("timestamp", LongType(), True),       # Thời gian sự kiện (Unix timestamp milliseconds)
    ])
    
    print("✓ Schema đã được định nghĩa:")
    print("  - user_id: IntegerType")
    print("  - movie_id: IntegerType")
    print("  - event_type: StringType")
    print("  - timestamp: LongType (milliseconds)\n")
    
    # Bước 4: Parse dữ liệu JSON từ Kafka message
    # Kafka message có format: key, value, topic, partition, offset, timestamp
    # Chúng ta quan tâm đến 'value' - nơi chứa dữ liệu JSON
    print("=" * 60)
    print("Bước 4: Parse dữ liệu JSON từ Kafka message")
    print("=" * 60)
    
    # Chuyển đổi value từ binary sang string
    # Sau đó parse JSON theo schema đã định nghĩa
    parsed_events_df = kafka_stream_df \
        .selectExpr("CAST(value AS STRING)") \
        .withColumn("data", from_json(col("value"), ratings_schema)) \
        .select("data.*")
    
    print("✓ Dữ liệu JSON đã được parse thành công\n")
    
    # Bước 5: Chuyển đổi và làm sạch dữ liệu
    # Filter chỉ lấy events có event_type = "click" hoặc "watch"
    # Chuyển đổi thành rating: click = 4.0, watch = 5.0
    # Convert timestamp từ Unix timestamp (milliseconds) sang TimestampType
    # Chia cho 1000 để chuyển từ milliseconds sang seconds
    print("=" * 60)
    print("Bước 5: Filter và chuyển đổi dữ liệu")
    print("=" * 60)
    print("Filter: Chỉ lấy event_type = 'click' hoặc 'watch'")
    print("Rating: click = 4.0, watch = 5.0")
    print("Timestamp: milliseconds -> TimestampType (seconds)")
    
    transformed_ratings_df = parsed_events_df \
        .filter((col("event_type") == "click") | (col("event_type") == "watch")) \
        .withColumn("rating", when(col("event_type") == "click", lit(4.0))
                           .when(col("event_type") == "watch", lit(5.0))) \
        .withColumn("timestamp", (col("timestamp") / 1000).cast(TimestampType())) \
        .select(
            "user_id",
            "movie_id",
            "rating",
            "timestamp"
        )
    
    print("✓ Dữ liệu đã được filter và chuyển đổi:")
    print("  - Filter: event_type == 'click' OR event_type == 'watch'")
    print("  - rating: click = 4.0, watch = 5.0")
    print("  - timestamp: milliseconds / 1000 -> TimestampType\n")
    
    # Bước 6: Định nghĩa hàm ghi dữ liệu vào PostgreSQL
    # foreachBatch cho phép xử lý từng batch dữ liệu
    # Mỗi khi có message mới, hàm này sẽ được gọi
    print("=" * 60)
    print("Bước 6: Chuẩn bị ghi dữ liệu vào PostgreSQL")
    print("=" * 60)
    print(f"Database URL: {DB_URL}")
    print(f"Target Table: {DB_TABLE}\n")
    
    def write_ratings_to_postgres(batch_df, epoch_id):
        """
        Hàm này được gọi cho mỗi micro-batch của streaming data
        
        Parameters:
        - batch_df: DataFrame chứa dữ liệu của batch hiện tại
        - epoch_id: ID của batch (tăng dần theo thời gian)
        """
        
        # Kiểm tra xem batch có dữ liệu không
        record_count = batch_df.count()
        
        if record_count > 0:
            print(f"\n{'='*60}")
            print(f"Epoch {epoch_id}: Đang xử lý {record_count} ratings mới")
            print(f"{'='*60}")
            
            # Hiển thị một vài record mẫu để debug (trước khi convert)
            print("Sample data (before conversion):")
            batch_df.show(5, truncate=False)
            
            # Chuyển đổi timestamp từ TimestampType về Unix timestamp (integer)
            # unix_timestamp() trả về seconds, nhân 1000 để có milliseconds
            batch_df_converted = batch_df \
                .withColumn("timestamp", (unix_timestamp(col("timestamp")) * 1000).cast("long"))
            
            print("Sample data (after conversion to Unix timestamp):")
            batch_df_converted.show(5, truncate=False)
            
            # Ghi dữ liệu vào PostgreSQL
            # mode("append"): Thêm dữ liệu mới vào bảng, không ghi đè
            batch_df_converted.write \
                .format("jdbc") \
                .option("url", DB_URL) \
                .option("dbtable", DB_TABLE) \
                .option("user", DB_USER) \
                .option("password", DB_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            print(f"✓ Đã ghi thành công {record_count} ratings vào bảng {DB_TABLE}")
            print(f"{'='*60}\n")
        else:
            print(f"Epoch {epoch_id}: Không có dữ liệu mới trong batch này")
    
    # Bước 7: Bắt đầu streaming query
    # writeStream: Bắt đầu ghi streaming data
    # outputMode("update"): Ghi các row đã update
    # foreachBatch: Xử lý từng batch bằng hàm đã định nghĩa
    print("=" * 60)
    print("Bước 7: Bắt đầu Streaming Query")
    print("=" * 60)
    print(f"Streaming đang chạy và đợi message mới từ topic '{KAFKA_TOPIC}'...")
    print("Nhấn Ctrl+C để dừng\n")
    
    query = transformed_ratings_df \
        .writeStream \
        .outputMode("update") \
        .foreachBatch(write_ratings_to_postgres) \
        .option("checkpointLocation", "/tmp/checkpoint/ratings") \
        .start()
    
    # checkpointLocation: Lưu trạng thái xử lý để có thể recovery khi bị lỗi
    # Spark sẽ nhớ message nào đã được xử lý
    
    print("✓ Streaming Query đã được khởi động thành công!")
    print("✓ Hệ thống đang lắng nghe và xử lý message real-time...\n")
    
    # Bước 8: Chờ đợi và xử lý liên tục
    # awaitTermination(): Giữ cho chương trình chạy mãi mãi
    # Chỉ dừng khi có lỗi hoặc người dùng dừng thủ công (Ctrl+C)
    print("=" * 60)
    print("Bước 8: Chạy liên tục và đợi message mới")
    print("=" * 60)
    print("Hệ thống đang hoạt động 24/7...")
    print(f"Mỗi khi có message 'click' hoặc 'watch' trong topic '{KAFKA_TOPIC}',")
    print("dữ liệu sẽ tự động được lưu vào database.\n")
    
    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Đã nhận tín hiệu dừng từ người dùng")
        print("Đang dừng Streaming Query...")
        print("=" * 60)
        query.stop()
        print("✓ Streaming Query đã dừng thành công")
    except Exception as e:
        print(f"\n\n❌ Lỗi xảy ra: {str(e)}")
        query.stop()
        raise


if __name__ == "__main__":
    # Kiểm tra biến môi trường để quyết định chạy hàm nào
    # RUN_MODE có thể là: "user_events" hoặc "ratings" (default)
    run_mode = os.environ.get('RUN_MODE', 'ratings')
    
    if run_mode == 'user_events':
        print("🚀 Starting User Events Subscriber...")
        print("=" * 60)
        subscribe_user_events()
    else:
        print("🚀 Starting Ratings Processor (Main)...") 
        print("=" * 60)
        main()