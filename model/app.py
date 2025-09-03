from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import spacy
import torch, os, json
import simplify_sentences
app = FastAPI()

spacy.prefer_gpu()
sentences  = None
#sentence_splitter = simplify_sentences.AssertionOptimizedSentenceSplitter()

# Load from /models instead of Hugging Face cache
def load_model_and_tokenizer(local_path):
    tokenizer = AutoTokenizer.from_pretrained(local_path)
    model = AutoModelForSequenceClassification.from_pretrained(local_path)
    return tokenizer, model

# Preload models
roberta_tokenizer, roberta_model = load_model_and_tokenizer("/models/roberta-large-mnli")
deberta_tokenizer, deberta_model = load_model_and_tokenizer("/models/claimbuster-deberta-v2")

# Load SpaCy
nlp = spacy.load("en_core_web_trf")
sentence_splitter = simplify_sentences.AssertionOptimizedSentenceSplitter(nlp)

def atomic_sentences(text):
    global sentences
    candidates = sentence_splitter.get_assertion_candidates(text)
    print(json.dumps(candidates, indent = 2))
    sentences = [x['text'] for x in candidates]

class QueryText(BaseModel):
    text: str

@app.post("/query/claims")
async def extract_claims(query: QueryText):
    global sentences
    if not sentences:
        atomic_sentences(query.text)

    claims = []

    for sent in sentences:

        inputs = deberta_tokenizer(sent, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = deberta_model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1).tolist()[0]
        if scores[0] >= 0.5:
            claims.append({"sentence": sent, "claimbuster_scores": scores})

    return {"claims": claims}
