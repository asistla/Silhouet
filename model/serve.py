# model/serve.py
import json, uvicorn, os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, util
from silhouet_config import *
from torch import mean as torchmean
from typing import Dict
import numpy as np
import torch

app = FastAPI()

# --- Load embedding model and vectors ---

MODEL = SentenceTransformer("all-mpnet-base-v2")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# The following lines for tokenizer and AutoModel seem redundant if SentenceTransformer is used directly.
# Using model.encode() from SentenceTransformer is the standard practice.
# tokenizer = AutoTokenized.from_pretrained(MODEL)
# model = AutoModel.from_pretrained(MODEL).to(DEVICE)
MODEL.to(DEVICE) # Ensure model is on the correct device

key_vectors = {}
mask_vectors = {}

# Config
RELEVANCE_SOFT_START = 0.2
RELEVANCE_HARD_CUTOFF = 0.05
SENSITIVITY_FACTORS: Dict[str, float] = {
    "relationship_satisfaction": 0.7,
    "resentment": 0.9,
    # default 1.0 for others
}

for key in PERSONALITY_KEYS:
    pos_examples = [PERSONALITY_LABEL_MAP[key][0]]
    neg_examples = [PERSONALITY_LABEL_MAP[key][1]]

    pos_embeddings = MODEL.encode(pos_examples, convert_to_tensor=True, device=DEVICE)
    neg_embeddings = MODEL.encode(neg_examples, convert_to_tensor=True, device=DEVICE)

    pos_vector = torchmean(pos_embeddings, dim=0, keepdim=True)
    neg_vector = torchmean(neg_embeddings, dim=0, keepdim=True)

    key_vectors[key] = {
        "positive": pos_vector,
        "negative": neg_vector,
    }

    mask_phrases = SENSITIVITY_MASKS.get(key)
    if mask_phrases:
        mask_embeds = MODEL.encode(mask_phrases, convert_to_tensor=True, device=DEVICE)
        mask_vectors[key] = mask_embeds

# --- API setup ---
class ScoreRequest(BaseModel):
    text: str

@app.post("/score")
async def score_text(request: ScoreRequest):
    text = request.text
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    print(f"[Scoring] Full text: {text[:80]}...")

    # 1. Generate a single embedding for the entire document.
    doc_embedding = MODEL.encode(text, convert_to_tensor=True, device=DEVICE)

    final_scores = {key: 0.0 for key in PERSONALITY_KEYS}

    # 2. Loop through each personality key to score the document embedding.
    for key in PERSONALITY_KEYS:
        # 3. Perform relevance check for the entire document.
        if key in mask_vectors:
            sims = util.cos_sim(doc_embedding, mask_vectors[key]).cpu().numpy().flatten()
            relevance = float(max(sims))
        else:
            relevance = 1.0 # Default relevance if no mask is defined.

        # 4. Apply relevance as a gate: skip if below hard cutoff.
        if relevance < RELEVANCE_HARD_CUTOFF:
            print(f"  {key}: relevance={relevance:.3f} (below hard cutoff, skipped)")
            continue # Score for this key remains 0.0

        # Calculate weight if relevance passes the gate.
        if relevance < RELEVANCE_SOFT_START:
            weight = (relevance - RELEVANCE_HARD_CUTOFF) / (RELEVANCE_SOFT_START - RELEVANCE_HARD_CUTOFF)
        else:
            weight = 1.0

        # 5. Calculate the holistic score for the document.
        pos_vector = key_vectors[key]["positive"]
        neg_vector = key_vectors[key]["negative"]
        pos_similarity = util.cos_sim(doc_embedding, pos_vector).item()
        neg_similarity = util.cos_sim(doc_embedding, neg_vector).item()
        raw_score = pos_similarity - neg_similarity

        sensitivity = SENSITIVITY_FACTORS.get(key, 1.0)
        adjusted_score = raw_score * weight * sensitivity

        # Assign the final calculated score directly.
        final_scores[key] = adjusted_score

        print(f"  {key}: relevance={relevance:.3f}, weight={weight:.3f}, "
              f"pos_sim={pos_similarity:.3f}, neg_sim={neg_similarity:.3f}, "
              f"raw={raw_score:.3f}, sensitivity={sensitivity}, "
              f"adj={adjusted_score:.3f}")

    # 6. Softmax normalization (this part remains the same).
    score_values = np.array(list(final_scores.values()))

    # Check if there are any non-zero scores to avoid division by zero
    if np.any(score_values != 0):
        exp_scores = np.exp(score_values - np.max(score_values))
        softmax_scores = SCALE_FACTOR * exp_scores / exp_scores.sum()
        normalized_scores = dict(zip(final_scores.keys(), softmax_scores.tolist()))
    else:
        # If all scores are zero, normalization results in zeros.
        normalized_scores = final_scores

    return json.dumps({"scores": normalized_scores})

# --- Averaging function for backend ---
# This function is unchanged.
def update_running_average(current_avg: float, count: int, new_score: float) -> float:
    return round(((current_avg * count) + new_score) / (count + 1), 4)

if __name__ == '__main__':
    uvicorn.run(app, host = '0.0.0.0', port = 8001)
