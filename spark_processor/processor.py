import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, lit
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

def main():
    print("Khởi động Spark Streaming Processor...")
    
    spark = SparkSession \
        .builder \
        .appName("KafkaToPostgres") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN") # Giảm bớt log
    
    # 1. Đọc stream từ Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    print("Đã kết nối stream Kafka...")

    # 2. Định nghĩa Schema cho JSON payload
    schema = StructType([
        StructField("user_id", IntegerType(), True),
        StructField("movie_id", IntegerType(), True),
        StructField("event_type", StringType(), True),
        StructField("timestamp", LongType(), True),
    ])

    # 3. Parse JSON từ 'value' của Kafka
    df_json = df.selectExpr("CAST(value AS STRING)") \
        .withColumn("data", from_json(col("value"), schema)) \
        .select("data.*")

    # 4. Biến đổi dữ liệu
    # Giả định: 'click' = rating 4.0, 'watch' = rating 5.0
    # Chúng ta chỉ lưu các sự kiện 'click' vào bảng ratings
    df_transformed = df_json \
        .filter(col("event_type") == "click") \
        .withColumn("rating", lit(4.0)) \
        .withColumn("timestamp", col("timestamp").cast(TimestampType())) \
        .select("user_id", "movie_id", "rating", "timestamp")

    print("Đang chờ dữ liệu...")
    
    # 5. Ghi stream vào Postgres (dùng foreachBatch)
    def write_to_postgres(batch_df, epoch_id):
        # Ghi batch_df vào Postgres
        batch_df.write \
            .format("jdbc") \
            .option("url", DB_URL) \
            .option("dbtable", DB_TABLE) \
            .option("user", DB_USER) \
            .option("password", DB_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
        print(f"Đã ghi {batch_df.count()} records vào Postgres (Epoch: {epoch_id}).")

    query = df_transformed.writeStream \
        .outputMode("update") \
        .foreachBatch(write_to_postgres) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()