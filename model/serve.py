# model/serve.py
import json, uvicorn, os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, util
from silhouet_config import *
from torch import mean as torchmean
app = FastAPI()

class ScoreRequest(BaseModel):
    text: str
# --- Load embedding model ---
model = SentenceTransformer("all-mpnet-base-v2")
key_vectors = {}
for key in PERSONALITY_KEYS:
    # Get all positive and negative examples for the current key
    pos_examples = [PERSONALITY_LABEL_MAP[key][0]]  # Or loop through all positive examples
    neg_examples = [PERSONALITY_LABEL_MAP[key][1]]  # Or loop through all negative examples

    # Encode all examples for a trait
    pos_embeddings = model.encode(pos_examples, convert_to_tensor=True)
    neg_embeddings = model.encode(neg_examples, convert_to_tensor=True)

    # Calculate the mean embedding for each
    pos_vector = torchmean(pos_embeddings, dim=0, keepdim=True)
    neg_vector = torchmean(neg_embeddings, dim=0, keepdim=True)

    # Store both the positive and negative vectors
    key_vectors[key] = {
        "positive": pos_vector,
        "negative": neg_vector,
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
    sentiment_scores = {}
    # Cosine similarity to each sentiment prompt
    for key in PERSONALITY_KEYS:
        pos_vector = key_vectors[key]["positive"]
        neg_vector = key_vectors[key]["negative"]

        # Calculate cosine similarity for both positive and negative
        pos_similarity = util.cos_sim(post_embedding, pos_vector).item()
        neg_similarity = util.cos_sim(post_embedding, neg_vector).item()

        # Calculate the bipolar score and add to the dictionary
        sentiment_scores[key] = pos_similarity - neg_similarity

    return json.dumps({"scores": sentiment_scores})

# --- Averaging function for backend ---
def update_running_average(current_avg: float, count: int, new_score: float) -> float:
    return round(((current_avg * count) + new_score) / (count + 1), 4)

def main():
    uvicorn.run(app, host='0.0.0.0', port=8001) # debug=True for local dev

if __name__ == '__main__':
    main()

