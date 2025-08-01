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

@app.post('/score')
async def score_text(request: ScoreRequest):
    text = request.text
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    print(f"Model service received text: '{text[:50]}...'") # Log received text for debugging

    # The actual scores are simple hashes/lengths for demonstration.
    scores = classifier(text, PERSONALITY_KEYS)
    scores = dict(zip(scores['labels'], scores['scores']))

    print(f"Model service returning scores for '{text[:20]}...'")
    print(json.dumps(scores, indent = 2))
    return json.dumps({"scores": scores})

def main():
    uvicorn.run(app, host='0.0.0.0', port=8001) # debug=True for local dev

if __name__ == '__main__':
    main()
