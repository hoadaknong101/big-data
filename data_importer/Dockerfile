FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install pandas sqlalchemy psycopg2-binary
CMD ["python", "import_data.py"]