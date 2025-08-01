# model/serve.py
#from flask import Flask, request, jsonify
import json, uvicorn, os, nltk
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from silhouet_config import *

app = FastAPI()

# --- Initialize NLP models/analyzers at startup ---
classifier = None
vader_analyzer = None

class ScoreRequest(BaseModel):
    text: str

@app.post('/score')
async def score_text(request: ScoreRequest):
    text = request.text
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    print(f"Model service received text: '{text[:50]}...'") # Log received text for debugging

    # --- PoC: Mocked NLP Logic ---
    # The actual scores are simple hashes/lengths for demonstration.
    scores = {}
    for i in range(1, 5):
        # Generate a semi-random but consistent score for the text for testing purposes
        score = (hash(text) % (i * 100)) / 100.0
        scores[f"sentiment_axis_{i}"] = max(0.0, min(1.0, score / 57.0)) # Normalize to 0-1 range

    # Example specific axes for easy identification
    scores['intellectual_honesty'] = (len(text) % 7) / 7.0
    scores['courage'] = (len(text) % 3) / 3.0
    scores['overall_positivity'] = (len(text) % 10) / 10.0
    scores['overall_negativity'] = (10 - (len(text) % 10)) / 10.0

    # Ensure all 57 are covered if needed, for now just demonstrate structure
    # For PoC, it's fine if not all 57 are unique, just demonstrating the structure.
    # --- End Mocked NLP Logic ---
    print(f"Model service returning scores for '{text[:20]}...'")
    return json.dumps({"scores": scores})

def main():
    uvicorn.run(app, host='0.0.0.0', port=8001) # debug=True for local dev

if __name__ == '__main__':
    main()
