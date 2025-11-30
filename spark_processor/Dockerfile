FROM apache/spark:3.5.0-scala2.12-java11-python3-ubuntu

USER root

# Set timezone to Vietnam (Ho Chi Minh City)
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Cài đặt các dependencies cần thiết
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python libraries
RUN pip install --no-cache-dir \
    psycopg2-binary \
    kafka-python

# Copy application code
COPY processor.py /app/processor.py
COPY run_user_events_subscriber.py /app/run_user_events_subscriber.py

# Set working directory
WORKDIR /app

# Đảm bảo files có quyền execute
RUN chmod +x /app/processor.py /app/run_user_events_subscriber.py

# Keep container running
CMD ["tail", "-f", "/dev/null"]