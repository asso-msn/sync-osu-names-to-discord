FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

ENV DB_PATH=/data/save.json
VOLUME /data

ENTRYPOINT ["python", "main.py"]
