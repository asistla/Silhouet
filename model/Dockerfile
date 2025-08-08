# model/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
#
EXPOSE 8001
#
#CMD ["python", "serve.py"]


# Set environment variable for Hugging Face cache
ENV HF_HOME ./hf_cache
# Create a directory for the cache
RUN mkdir -p ./hf_cache

# Command to run the FastAPI application directly using uvicorn
# This tells uvicorn to look for an 'app' object within the 'app' module (i.e., app.py)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
