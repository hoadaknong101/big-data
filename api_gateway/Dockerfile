FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install Flask pymilvus sqlalchemy psycopg2-binary kafka-python pandas
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]