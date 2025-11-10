FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install torch pandas sqlalchemy psycopg2-binary pymilvus
CMD ["python", "train.py"]