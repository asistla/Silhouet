import spacy
from sentence_transformers import SentenceTransformer, util
from sentence_simplifier import SentenceSimplifier

class ClaimExtractor:
    def __init__(self, similarity_threshold=0.85):
        self.nlp = spacy.load("en_core_web_sm")
        self.simplifier = SentenceSimplifier(self.nlp)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        self.similarity_threshold = similarity_threshold
        self.claims = []  # canonicalized claims

    def is_feeling_or_preference(self, doc):
        if not doc:
            return False

        if any(t.lemma_ == "i" for t in doc) and any(
            t.lemma_ in ["feel", "like", "love", "hate"] for t in doc):
                return True
        return False

    def is_personal_event(self, doc):
        # heuristic: "I + past tense verb" or contains specific time references
        if doc[0].lemma_.lower() == "i" and any(t.tag_ in ["VBD", "VBN"] for t in doc):
            return True
        return False

    def is_established_event(self, sentence):
        # placeholder: this eventually checks against curated "known events" KB
        return False  # for now, assume no

    def normalize_claim(self, sentence):
        return sentence.lower().strip()

    def collapse_similar(self, new_claim):
        if not self.claims:
            self.claims.append(new_claim)
            return

        embeddings = self.embedder.encode([c for c in self.claims] + [new_claim], convert_to_tensor=True)
        sims = util.cos_sim(embeddings[-1], embeddings[:-1])[0]

        if sims.max() < self.similarity_threshold:
            self.claims.append(new_claim)

    def extract_claims(self, text):
        sents = self.simplifier.simplify(text)
        for sent in sents:
            doc = self.nlp(sent)
            if self.is_feeling_or_preference(doc): 
                continue
            if self.is_personal_event(doc): 
                continue
            if self.is_established_event(sent): 
                continue

            claim = self.normalize_claim(sent)
            self.collapse_similar(claim)

        return set(self.claims)
