FROM bitnami/spark:3.5

USER root
# Cài đặt python (đã có) và các thư viện cần thiết
RUN pip install psycopg2-binary
USER 1001

COPY processor.py /app/processor.py