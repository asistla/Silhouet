# model/Dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# System deps
RUN apt-get update && apt-get install -y git wget curl python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Python deps (pin versions for reproducibility)
# Note: sentence-transformers will install a compatible transformers version.
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.6 \
    sentence-transformers \
    spacy==3.7.4 \
    nltk \
    pysbd

# Download SpaCy model
RUN python -m spacy download en_core_web_trf
# NLTK data is needed for simplify_sentences.py
RUN python -c "import nltk; nltk.download('punkt')"

# Create directory for local models
RUN mkdir -p /models

# Set Hugging Face cache directory to /models to ensure models are saved there
ENV HF_HOME=/models

# Pre-download the required Hugging Face model into /models
# We are only using claimbuster-deberta-v2 now.
RUN python - <<EOF
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Define the model to download
model_name = "whispAI/ClaimBuster-DeBERTaV2"
local_dir = "/models/claimbuster-deberta-v2"

# Create directory and download model
os.makedirs(local_dir, exist_ok=True)
AutoTokenizer.from_pretrained(model_name, use_safetensors=True).save_pretrained(local_dir)
AutoModelForSequenceClassification.from_pretrained(model_name, use_safetensors=True).save_pretrained(local_dir)
EOF

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared configuration and the rest of the application code
# This ensures silhouet_config.py and simplify_sentences.py are available
COPY ./shared_config /app/shared_config
COPY . .

EXPOSE 8001

# Command to run the unified FastAPI application in serve.py
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8001"]
