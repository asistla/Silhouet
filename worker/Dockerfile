# silhouet/worker/Dockerfile (updated paths)
FROM python:3.10-alpine

WORKDIR /app

# Install system dependencies for psycopg2-binary
RUN apk add --no-cache postgresql-client build-base

# Copy worker-specific requirements (relative to the build context: ./)
COPY worker/requirements.txt .
COPY ./shared_config/silhouet_config.py .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip list
# Copy the backend application code from the root context
COPY backend/ /app/backend_code/

# Set Python path
ENV PYTHONPATH /app/backend_code/
