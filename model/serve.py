# model/serve.py
import json, uvicorn, os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, util
from silhouet_config import *
from torch import mean as torchmean
import re
from typing import Dict
import numpy as np
import spacy

app = FastAPI()
class ScoreRequest(BaseModel):
    text: str


# --- Load embedding model ---
model = SentenceTransformer("all-mpnet-base-v2")
nlp = spacy.load("en_core_web_sm")

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

    mask_phrases = SENSITIVITY_MASKS.get(key)
    if mask_phrases:
        mask_embeds = model.encode(mask_phrases, convert_to_tensor = True)
        mask_vectors[key] = mask_embeds

# --- API setup ---
app = FastAPI()

class ScoreRequest(BaseModel):
    text: str

@app.post("/score")
async def score_text(request: ScoreRequest):
    text = request.text
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    #print(f"[Scoring] Text: {text[:60]}...")

    sentences = re.findall('\w+', text) #split_sentences(text)
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    if not sentences:
        return json.dumps({"scores": {k: 0.0 for k in PERSONALITY_KEYS}})

    aggregated_scores = {key: 0.0 for key in PERSONALITY_KEYS}
    total_weights = {key: 0.0 for key in PERSONALITY_KEYS}

    for sent in sentences:
        sent_embedding = model.encode(sent, convert_to_tensor=True)
        sent_len = len(sent.split())

        print(f"\n[Sentence] \"{sent}\" (len={sent_len} words)")

        for key in PERSONALITY_KEYS:
            # --- Relevance check ---
            if key in mask_vectors:
                sims = util.cos_sim(sent_embedding, mask_vectors[key]).cpu().numpy().flatten()
                relevance = float(max(sims))
            else:
                relevance = 1.0

            if relevance < RELEVANCE_HARD_CUTOFF:
                print(f"  {key}: relevance={relevance:.3f} (below hard cutoff, skipped)")
                continue
            elif relevance < RELEVANCE_SOFT_START:
                weight = (relevance - RELEVANCE_HARD_CUTOFF) / (RELEVANCE_SOFT_START - RELEVANCE_HARD_CUTOFF)
            else:
                weight = 1.0

            # Cosine similarity
            pos_vector = key_vectors[key]["positive"]
            neg_vector = key_vectors[key]["negative"]
            pos_similarity = util.cos_sim(sent_embedding, pos_vector).item()
            neg_similarity = util.cos_sim(sent_embedding, neg_vector).item()
            raw_score = pos_similarity - neg_similarity

            sensitivity = SENSITIVITY_FACTORS.get(key, 1.0)
            adjusted_score = raw_score * weight * sensitivity

            # Log debug info
            print(f"  {key}: relevance={relevance:.3f}, weight={weight:.3f}, "
                  f"pos_sim={pos_similarity:.3f}, neg_sim={neg_similarity:.3f}, "
                  f"raw={raw_score:.3f}, sensitivity={sensitivity}, "
                  f"adj={adjusted_score:.3f}")

            # Aggregate
            aggregated_scores[key] += adjusted_score * sent_len
            total_weights[key] += sent_len

    # Finalize averages
    final_scores = {}
    for key in PERSONALITY_KEYS:
        if total_weights[key] > 0:
            final_scores[key] = aggregated_scores[key] / total_weights[key]
        else:
            final_scores[key] = 0.0

    # Softmax normalization
    score_values = np.array(list(final_scores.values()))
    exp_scores = np.exp(score_values - np.max(score_values))
    softmax_scores = SCALE_FACTOR * exp_scores / exp_scores.sum()
    final_scores = dict(zip(final_scores.keys(), softmax_scores.tolist()))

    return json.dumps({"scores": final_scores})

# --- Averaging function for backend ---
def update_running_average(current_avg: float, count: int, new_score: float) -> float:
    return round(((current_avg * count) + new_score) / (count + 1), 4)

def main():
    uvicorn.run(app, host='0.0.0.0', port=8001) # debug=True for local dev

if __name__ == '__main__':
    main()

