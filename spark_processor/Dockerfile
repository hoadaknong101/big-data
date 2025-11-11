FROM apache/spark:3.5.0-scala2.12-java11-python3-ubuntu

USER root

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

# Set working directory
WORKDIR /app

# Đảm bảo file có quyền execute
RUN chmod +x /app/processor.py

# Keep container running
CMD ["tail", "-f", "/dev/null"]