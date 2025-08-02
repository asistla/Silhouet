# model/serve.py
#from flask import Flask, request, jsonify
import json, uvicorn, os, nltk
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from transformers import pipeline
from silhouet_config import *

app = FastAPI()

# --- Initialize NLP models/analyzers at startup ---
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

class ScoreRequest(BaseModel):
    text: str
# --- Load embedding model ---
model = SentenceTransformer("all-mpnet-base-v2")

# --- Precompute positive prompt embeddings ---
key_embeddings = {
    key: model.encode(PERSONALITY_LABEL_MAP[key][0], convert_to_tensor=True)
    for key in PERSONALITY_KEYS
}

# --- API setup ---
app = FastAPI()

class ScoreRequest(BaseModel):
    text: str

@app.post("/score")
async def score_text(request: ScoreRequest):
    text = request.text
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    print(f"[Scoring] Text: {text[:60]}...")

    # Embed post
    post_embedding = model.encode(text, convert_to_tensor=True)

    # Cosine similarity to each sentiment prompt
    scores = {
        key: float(util.cos_sim(post_embedding, prompt_embedding))
        for key, prompt_embedding in key_embeddings.items()
    }

    # Normalize [-1, 1] → [0, 1], round to 4 digits
    normalized_scores = {
        key: round((score + 1) / 2, 4) for key, score in scores.items()
    }

    return {"scores": normalized_scores}

# --- Averaging function for backend ---
def update_running_average(current_avg: float, count: int, new_score: float) -> float:
    return round(((current_avg * count) + new_score) / (count + 1), 4)

def main():
    uvicorn.run(app, host='0.0.0.0', port=8001) # debug=True for local dev

if __name__ == '__main__':
    main()

