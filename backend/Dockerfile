# backend/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt ./
COPY silhouet_config.py .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
