# model/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt ./
COPY silhouet_config.py .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "serve.py"]
