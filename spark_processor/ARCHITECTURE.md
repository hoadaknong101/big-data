# Kiến Trúc Hệ Thống User Events Streaming

## Sơ Đồ Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KAFKA CLUSTER                                 │
│                                                                      │
│  Topic: user-events                                                  │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ Message Format (JSON):                                  │         │
│  │ {                                                       │         │
│  │   "user_id": 123,                                       │         │
│  │   "movie_id": 456,                                      │         │
│  │   "event_type": "click",                                │         │
│  │   "timestamp": 1701234567890                            │         │
│  │ }                                                       │         │
│  └────────────────────────────────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Subscribe (Real-time)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SPARK STREAMING PROCESSOR                          │
│                                                                      │
│  Function: subscribe_user_events()                                   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 1: Khởi tạo Spark Session                              │   │
│  │   - AppName: UserEventsSubscriber                           │   │
│  │   - Log Level: WARN                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 2: Kết nối Kafka                                       │   │
│  │   - readStream.format("kafka")                              │   │
│  │   - subscribe("user-events")                                │   │
│  │   - startingOffsets("latest")                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 3: Định nghĩa Schema                                   │   │
│  │   - user_id: IntegerType                                    │   │
│  │   - movie_id: IntegerType                                   │   │
│  │   - event_type: StringType                                  │   │
│  │   - timestamp: LongType                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 4: Parse JSON                                          │   │
│  │   - CAST(value AS STRING)                                   │   │
│  │   - from_json(col("value"), schema)                         │   │
│  │   - select("data.*")                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 5: Transform Data                                      │   │
│  │   - timestamp → event_timestamp (TimestampType)             │   │
│  │   - Thêm cột processed_at (current_timestamp)               │   │
│  │   - Select columns                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 6: Write Function                                      │   │
│  │   write_user_events_to_postgres(batch_df, epoch_id)         │   │
│  │   - Count records                                           │   │
│  │   - Show sample data                                        │   │
│  │   - Write to JDBC                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 7: Start Streaming                                     │   │
│  │   - writeStream.outputMode("append")                        │   │
│  │   - foreachBatch(write_function)                            │   │
│  │   - checkpointLocation("/tmp/checkpoint/user-events")       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           │                                          │
│                           ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ BƯỚC 8: Await Termination                                   │   │
│  │   - query.awaitTermination()                                │   │
│  │   - Chạy liên tục 24/7                                      │   │
│  │   - Exception handling (Ctrl+C, errors)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ JDBC Write (Batch)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                             │
│                                                                      │
│  Table: user_events                                                  │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ Columns:                                                │         │
│  │   - id (SERIAL PRIMARY KEY)                             │         │
│  │   - user_id (INTEGER)                                   │         │
│  │   - movie_id (INTEGER)                                  │         │
│  │   - event_type (VARCHAR)                                │         │
│  │   - event_timestamp (TIMESTAMP)                         │         │
│  │   - processed_at (TIMESTAMP)                            │         │
│  │   - created_at (TIMESTAMP)                              │         │
│  │                                                         │         │
│  │ Indexes:                                                │         │
│  │   - idx_user_events_user_id                             │         │
│  │   - idx_user_events_movie_id                            │         │
│  │   - idx_user_events_event_type                          │         │
│  │   - idx_user_events_timestamp                           │         │
│  │   - idx_user_events_user_movie (composite)              │         │
│  │   - idx_user_events_user_type (composite)               │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
│  Views:                                                              │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ user_events_stats                                       │         │
│  │   - Thống kê theo event_type                            │         │
│  │   - Total events, unique users, unique movies           │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
│  Functions:                                                          │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ get_recent_events(limit)                                │         │
│  │ get_user_events(user_id, limit)                         │         │
│  └────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

## Luồng Dữ Liệu Chi Tiết

```
Producer (Web Client)
    │
    │ POST /event
    │ {user_id, movie_id, event_type, timestamp}
    │
    ▼
API Gateway
    │
    │ Publish message
    │
    ▼
Kafka Topic: user-events
    │
    │ Real-time streaming
    │ (Micro-batches every few seconds)
    │
    ▼
Spark Streaming
    │
    ├─► Read from Kafka
    ├─► Parse JSON
    ├─► Transform data
    ├─► Batch processing
    │
    ▼
PostgreSQL
    │
    ├─► Table: user_events
    ├─► Indexes for fast queries
    └─► Views & Functions
```

## Timeline Xử Lý

```
T0: Message arrives in Kafka
    │
    ├─► Kafka stores message in partition
    │
T1: Spark reads message (micro-batch)
    │
    ├─► Parse JSON (< 1ms)
    ├─► Transform data (< 1ms)
    │
T2: Write to PostgreSQL
    │
    ├─► JDBC connection
    ├─► Batch insert
    ├─► Commit transaction
    │
T3: Data available in database
    │
    └─► Total latency: ~2-5 seconds
```

## Fault Tolerance

```
┌─────────────────────────────────────┐
│     Checkpoint Mechanism             │
├─────────────────────────────────────┤
│                                     │
│  /tmp/checkpoint/user-events/       │
│    ├─── offsets/                    │
│    │     └─── 0, 1, 2, ...          │
│    ├─── commits/                    │
│    └─── metadata                    │
│                                     │
│  Lưu trạng thái:                    │
│  - Kafka offset đã xử lý            │
│  - Batch ID                         │
│  - Metadata                         │
│                                     │
│  Khi restart:                       │
│  - Đọc checkpoint                   │
│  - Resume từ offset cuối            │
│  - Không mất dữ liệu                │
└─────────────────────────────────────┘
```

## Scaling Strategy

```
┌──────────────────────────────────────────────────────────┐
│              Horizontal Scaling                           │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Kafka Topic: user-events (3 partitions)                 │
│    ├─── Partition 0 ──► Spark Executor 1                │
│    ├─── Partition 1 ──► Spark Executor 2                │
│    └─── Partition 2 ──► Spark Executor 3                │
│                                                          │
│  Mỗi executor xử lý độc lập:                             │
│  - Read from assigned partition                          │
│  - Process independently                                 │
│  - Write to PostgreSQL                                   │
│                                                          │
│  Throughput tăng tuyến tính với số partitions            │
└──────────────────────────────────────────────────────────┘
```

## Monitoring Points

```
┌─────────────────────────────────────────────────────────┐
│                   Monitoring                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Kafka Metrics:                                      │
│     - Messages per second                               │
│     - Lag (offset difference)                           │
│     - Partition distribution                            │
│                                                         │
│  2. Spark Metrics:                                      │
│     - Processing time per batch                         │
│     - Records per batch                                 │
│     - Checkpoint status                                 │
│                                                         │
│  3. Database Metrics:                                   │
│     - Insert rate                                       │
│     - Table size                                        │
│     - Query performance                                 │
│                                                         │
│  4. Application Logs:                                   │
│     - Sample data per batch                             │
│     - Error messages                                    │
│     - Epoch ID tracking                                 │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────┐
│              Error Handling                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Try:                                                   │
│    query.awaitTermination()                             │
│      │                                                  │
│      ├─► Normal processing                              │
│      │                                                  │
│  Except KeyboardInterrupt:                              │
│      │                                                  │
│      ├─► Log: "Đã nhận tín hiệu dừng"                   │
│      ├─► query.stop()                                   │
│      └─► Graceful shutdown                              │
│                                                         │
│  Except Exception as e:                                 │
│      │                                                  │
│      ├─► Log error details                              │
│      ├─► query.stop()                                   │
│      └─► Raise exception                                │
│                                                         │
│  Checkpoint ensures:                                    │
│    - No data loss                                       │
│    - Resume from last processed offset                  │
└─────────────────────────────────────────────────────────┘
```
