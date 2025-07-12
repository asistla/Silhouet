# model/serve.py
from flask import Flask, request, jsonify
import json
app = Flask(__name__)
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import pipeline
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from silhouet_config import PERSONALITY_LABEL_MAP
# Import the shared configuration
from silhouet_config import PERSONALITY_KEYS

app = FastAPI()

# --- Initialize NLP models/analyzers at startup ---
classifier = None
vader_analyzer = None

# Mapping of your personality keys to zero-shot labels.
# Each value should be a tuple (positive_hypothesis, negative_hypothesis)
# The score will be derived from the confidence of the positive hypothesis.

@app.route('/score', methods=['POST'])
def score_text():
    data = request.json
    text = data.get('text')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    print(f"Model service received text: '{text[:50]}...'") # Log received text for debugging

    # --- PoC: Mocked NLP Logic ---
    # This simulates your NLP model returning 57 sentiment scores (0.0 to 1.0)
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
    return jsonify({"scores": scores})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True) # debug=True for local dev
