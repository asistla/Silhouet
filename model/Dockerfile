# model/Dockerfile
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

# System deps
RUN apt-get update && apt-get install -y \
    git wget curl python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Python deps (pin versions for reproducibility)
RUN pip install --no-cache-dir \
    fastapi==0.115.0 \
    uvicorn[standard]==0.30.6 \
    transformers==4.44.2 \
    spacy==3.7.4 \
    nltk \
    pysbd

# Download SpaCy model
RUN python -m spacy download en_core_web_trf
RUN python -c "import nltk; nltk.download('punkt_tab')"
RUN mkdir -p /models

#Set same env for huggingface cache
ENV HF_HOME ./models
# Pre-download Hugging Face models into /models
RUN python - <<EOF
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

models = {
    "roberta-large-mnli": "roberta-large-mnli",
    "claimbuster-deberta-v2": "whispAI/ClaimBuster-DeBERTaV2",
}

for name, repo in models.items():
    model_dir = f"/models/{name}"
    os.makedirs(model_dir, exist_ok=True)
    AutoTokenizer.from_pretrained(repo).save_pretrained(model_dir)
    AutoModelForSequenceClassification.from_pretrained(repo).save_pretrained(model_dir)
EOF

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001

# Command to run the FastAPI application directly using uvicorn
# This tells uvicorn to look for an 'app' object within the 'app' module (i.e., app.py)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
