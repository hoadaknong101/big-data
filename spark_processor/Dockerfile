# Dùng image apache/spark-py làm cơ sở
FROM apache/spark-py:v3.4.0

# Dịch vụ Spark chạy bằng user 'spark', nhưng chúng ta cần 'root' để cài đặt
USER root

# Cài đặt các thư viện (psycopg2)
# (Image này dựa trên Debian, dùng apt)
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip install psycopg2-binary && \
    apt-get clean

# Trở về user 'spark' để đảm bảo an toàn
USER ${SPARK_UID:-185}

# Copy file processor của bạn vào
COPY processor.py /app/processor.py