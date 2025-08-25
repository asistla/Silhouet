import spacy
import re
import hashlib
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import json

class ClaimType(Enum):
    FACTUAL = "factual"           # "The earth is round"
    EVALUATIVE = "evaluative"     # "Pizza is delicious" 
    PREDICTIVE = "predictive"     # "It will rain tomorrow"
    CAUSAL = "causal"            # "Smoking causes cancer"
    COMPARATIVE = "comparative"   # "X is better than Y"
    MODAL = "modal"              # "X might be true"
    NORMATIVE = "normative"      # "People should exercise"
    EXPERIENTIAL = "experiential" # "I feel sad"

class ClaimPolarity(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"

@dataclass
class SemanticClaim:
    """A semantically processed claim ready for aggregation"""
    raw_text: str
    normalized_text: str
    claim_type: ClaimType
    polarity: ClaimPolarity
    confidence: float
    
    # Semantic components
    subject: str = ""
    predicate: str = ""
    object: str = ""
    
    # Modifiers that affect meaning
    negated: bool = False
    temporal_qualifier: str = ""  # "always", "never", "sometimes"
    modal_strength: str = ""      # "might", "will", "could"
    
    # For aggregation
    semantic_hash: str = field(init=False)
    canonical_form: str = field(init=False)
    
    def __post_init__(self):
        self.canonical_form = self._create_canonical_form()
        self.semantic_hash = hashlib.md5(self.canonical_form.encode()).hexdigest()[:12]
    
    def _create_canonical_form(self) -> str:
        """Create a canonical form for semantic equivalence"""
        # Normalize subject/predicate/object
        subj = self._normalize_entity(self.subject)
        pred = self._normalize_predicate(self.predicate) 
        obj = self._normalize_entity(self.object)
        
        # Create structured representation
        parts = []
        if self.negated:
            parts.append("NOT")
        if self.temporal_qualifier:
            parts.append(self.temporal_qualifier.upper())
        if self.modal_strength:
            parts.append(self.modal_strength.upper())
            
        core = f"{subj}|{pred}|{obj}".strip("|")
        if parts:
            return f"[{' '.join(parts)}] {core}"
        return core
    
    def _normalize_entity(self, entity: str) -> str:
        """Normalize entity mentions for equivalence"""
        if not entity:
            return ""
        
        # Convert to lowercase
        entity = entity.lower().strip()
        
        # Handle common variations
        equivalences = {
            "the earth": "earth",
            "our planet": "earth", 
            "the world": "earth",
            "people": "humans",
            "folks": "humans",
            "individuals": "humans",
            "the government": "government",
            "politicians": "government",
            "covid-19": "covid",
            "coronavirus": "covid",
            "artificial intelligence": "ai",
            "climate change": "global warming"
        }
        
        return equivalences.get(entity, entity)
    
    def _normalize_predicate(self, predicate: str) -> str:
        """Normalize predicates for equivalence"""
        if not predicate:
            return ""
            
        pred = predicate.lower().strip()
        
        # Handle verb variations
        equivalences = {
            "is": "be",
            "are": "be", 
            "was": "be",
            "were": "be",
            "causes": "cause",
            "results in": "cause",
            "leads to": "cause",
            "makes": "cause",
            "likes": "like",
            "enjoys": "like",
            "loves": "like",
            "dislikes": "dislike",
            "hates": "dislike"
        }
        
        return equivalences.get(pred, pred)

class RobustClaimsExtractor:
    def __init__(self):
        # Load spaCy with additional components
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Please install: python -m spacy download en_core_web_sm")
            raise
            
        # Add custom components
        self._setup_patterns()
        self._setup_semantic_rules()
        
    def _setup_patterns(self):
        """Set up linguistic patterns for different claim types"""
        
        # Modal expressions and their strengths
        self.modal_expressions = {
            # Certainty markers
            'definitely': 'certain',
            'certainly': 'certain', 
            'obviously': 'certain',
            'clearly': 'certain',
            'undoubtedly': 'certain',
            
            # High probability  
            'probably': 'likely',
            'likely': 'likely',
            'most likely': 'likely',
            
            # Medium probability
            'possibly': 'possible',
            'perhaps': 'possible', 
            'maybe': 'possible',
            'might': 'possible',
            'could': 'possible',
            'may': 'possible',
            
            # Low probability
            'unlikely': 'unlikely',
            'doubtful': 'unlikely',
            'questionable': 'unlikely'
        }
        
        # Temporal qualifiers
        self.temporal_patterns = {
            'always': 'always',
            'never': 'never', 
            'usually': 'usually',
            'often': 'often',
            'sometimes': 'sometimes',
            'rarely': 'rarely',
            'occasionally': 'occasionally',
            'generally': 'generally',
            'typically': 'usually'
        }
        
        # Hedging expressions that indicate uncertainty
        self.hedging_patterns = [
            r'it seems? (?:that|like)',
            r'it appears? (?:that|like)', 
            r'i (?:think|believe|feel|guess|suspect) (?:that)?',
            r'in my (?:opinion|view)',
            r'from my perspective',
            r'it is (?:possible|likely|probable) that',
            r'one could argue (?:that)?',
            r'arguably',
            r'presumably'
        ]
        
        # Causal patterns
        self.causal_patterns = [
            r'(.+) (?:causes?|results? in|leads? to|brings about|produces?) (.+)',
            r'(.+) (?:because|due to|owing to|as a result of) (.+)',
            r'if (.+) then (.+)',
            r'(.+) makes (.+)',
            r'(.+) is (?:caused by|due to|because of) (.+)'
        ]
        
        # Comparative patterns
        self.comparative_patterns = [
            r'(.+) is (?:better|worse|superior|inferior) (?:than|to) (.+)',
            r'(.+) is (?:more|less) \w+ than (.+)',
            r'(.+) (?:exceeds?|surpasses?) (.+)',
            r'compared to (.+), (.+) is \w+'
        ]
        
        # Normative patterns (should/ought statements)
        self.normative_patterns = [
            r'(.+) should (.+)',
            r'(.+) ought to (.+)',
            r'(.+) must (.+)',
            r'it is (?:important|necessary|essential) (?:that|for) (.+)',
            r'(.+) need(?:s)? to (.+)'
        ]
    
    def _setup_semantic_rules(self):
        """Set up rules for semantic interpretation"""
        
        # Negation markers
        self.negation_markers = {
            'not', 'no', 'never', 'nothing', 'nobody', 'nowhere',
            'neither', 'none', 'cannot', 'can\'t', 'won\'t', 'wouldn\'t',
            'shouldn\'t', 'couldn\'t', 'isn\'t', 'aren\'t', 'wasn\'t',
            'weren\'t', 'don\'t', 'doesn\'t', 'didn\'t', 'haven\'t',
            'hasn\'t', 'hadn\'t'
        }
        
        # Intensifiers that affect claim strength
        self.intensifiers = {
            'very': 1.2,
            'extremely': 1.5,
            'incredibly': 1.5,
            'really': 1.1,
            'quite': 1.1,
            'somewhat': 0.8,
            'rather': 0.9,
            'pretty': 1.1,
            'totally': 1.4,
            'completely': 1.4,
            'absolutely': 1.5
        }
        
    def extract_claims(self, text: str, user_metadata: Dict = None) -> List[SemanticClaim]:
        """Extract and process claims from text"""
        
        # Preprocessing
        text = self._preprocess_text(text)
        
        # Sentence segmentation  
        sentences = self._segment_sentences(text)
        
        all_claims = []
        
        for sentence in sentences:
            # Skip very short or non-meaningful sentences
            if len(sentence.split()) < 3:
                continue
                
            # Linguistic simplification
            simple_sentences = self._simplify_sentence(sentence)
            
            # Extract semantic claims
            for simple_sent in simple_sentences:
                claims = self._extract_semantic_claims(simple_sent)
                all_claims.extend(claims)
        
        # Post-processing and filtering
        filtered_claims = self._filter_and_enhance_claims(all_claims)
        
        return filtered_claims
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize input text"""
        # Handle common contractions
        contractions = {
            "won't": "will not",
            "can't": "cannot", 
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _segment_sentences(self, text: str) -> List[str]:
        """Improved sentence segmentation"""
        doc = self.nlp(text)
        
        sentences = []
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Filter out non-sentences
            if len(sent_text) < 5:
                continue
            if sent_text.count(' ') < 1:  # Single words
                continue
                
            sentences.append(sent_text)
            
        return sentences
    
    def _simplify_sentence(self, sentence: str) -> List[str]:
        """Enhanced sentence simplification"""
        doc = self.nlp(sentence)
        
        # Find all clauses
        clauses = self._extract_all_clauses(doc)
        
        if len(clauses) <= 1:
            return [sentence]
            
        # Process each clause
        simplified = []
        for clause in clauses:
            clause_text = " ".join([token.text for token in clause])
            if self._is_meaningful_clause(clause_text):
                simplified.append(clause_text)
                
        return simplified if simplified else [sentence]
    
    def _extract_all_clauses(self, doc) -> List[List]:
        """Extract all clauses from dependency parse"""
        clauses = []
        processed = set()
        
        # Find all clause roots
        for token in doc:
            if token.i in processed:
                continue
                
            if token.dep_ in ["ROOT", "conj", "advcl", "ccomp", "xcomp", "acl", "relcl"]:
                clause_tokens = self._get_clause_span(token)
                if clause_tokens:
                    clauses.append(clause_tokens)
                    processed.update(t.i for t in clause_tokens)
                    
        return clauses
    
    def _get_clause_span(self, root_token) -> List:
        """Get all tokens belonging to a clause"""
        tokens = []
        
        def collect_subtree(token):
            tokens.append(token)
            for child in token.children:
                # Include most dependencies but exclude other clauses
                if child.dep_ not in ["conj", "advcl", "ccomp", "xcomp", "acl", "relcl"]:
                    collect_subtree(child)
        
        collect_subtree(root_token)
        return sorted(tokens, key=lambda x: x.i)
    
    def _is_meaningful_clause(self, clause_text: str) -> bool:
        """Check if clause is meaningful for claim extraction"""
        clause_text = clause_text.strip()
        
        # Too short
        if len(clause_text.split()) < 3:
            return False
            
        # Must have subject and verb
        doc = self.nlp(clause_text)
        has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] for token in doc)
        has_verb = any(token.pos_ in ["VERB", "AUX"] for token in doc)
        
        return has_subject and has_verb
    
    def _extract_semantic_claims(self, sentence: str) -> List[SemanticClaim]:
        """Extract semantically rich claims from a sentence"""
        doc = self.nlp(sentence)
        claims = []
        
        # Skip questions, commands, greetings
        if not self._is_propositional(sentence, doc):
            return claims
            
        # Detect claim type
        claim_type = self._classify_claim_type(sentence, doc)
        
        # Extract semantic components
        semantic_info = self._extract_semantic_components(doc)
        
        # Detect modifiers
        modifiers = self._extract_modifiers(sentence, doc)
        
        # Create semantic claim
        claim = SemanticClaim(
            raw_text=sentence,
            normalized_text=sentence.lower(),
            claim_type=claim_type,
            polarity=self._determine_polarity(doc, modifiers),
            confidence=self._calculate_confidence(claim_type, modifiers),
            subject=semantic_info.get('subject', ''),
            predicate=semantic_info.get('predicate', ''),
            object=semantic_info.get('object', ''),
            negated=modifiers.get('negated', False),
            temporal_qualifier=modifiers.get('temporal', ''),
            modal_strength=modifiers.get('modal', '')
        )
        
        claims.append(claim)
        return claims
    
    def _is_propositional(self, sentence: str, doc) -> bool:
        """Enhanced check for propositional content"""
        sentence = sentence.strip()
        
        # Questions
        if sentence.endswith('?') or sentence.lower().startswith(('what', 'why', 'how', 'when', 'where', 'who')):
            return False
            
        # Commands
        if any(token.dep_ == "ROOT" and token.tag_ in ["VB", "VBP"] for token in doc):
            if not any(token.dep_ in ["nsubj", "nsubjpass"] for token in doc):
                return False
                
        # Greetings and social expressions
        social_patterns = [
            r'^(?:hi|hello|hey|thanks|thank you|bye|goodbye)',
            r'^(?:good (?:morning|afternoon|evening|night))',
            r'^(?:sorry|excuse me|please)',
            r'^(?:yes|no|ok|okay)$'
        ]
        
        for pattern in social_patterns:
            if re.match(pattern, sentence.lower()):
                return False
                
        # Must express some kind of statement
        has_meaningful_content = (
            any(token.pos_ in ["NOUN", "PROPN", "ADJ"] for token in doc) and
            any(token.pos_ in ["VERB", "AUX"] for token in doc)
        )
        
        return has_meaningful_content
    
    def _classify_claim_type(self, sentence: str, doc) -> ClaimType:
        """Classify the type of claim"""
        sentence_lower = sentence.lower()
        
        # Causal claims
        if any(re.search(pattern, sentence_lower) for pattern in self.causal_patterns):
            return ClaimType.CAUSAL
            
        # Comparative claims  
        if any(re.search(pattern, sentence_lower) for pattern in self.comparative_patterns):
            return ClaimType.COMPARATIVE
            
        # Normative claims
        if any(re.search(pattern, sentence_lower) for pattern in self.normative_patterns):
            return ClaimType.NORMATIVE
            
        # Predictive claims (future tense)
        if any(token.text.lower() in ['will', 'shall', 'going to'] for token in doc):
            return ClaimType.PREDICTIVE
            
        # Experiential claims (first person + feeling/experience verbs)
        experiential_verbs = {'feel', 'think', 'believe', 'experience', 'sense', 'perceive'}
        has_first_person = any(token.text.lower() in ['i', 'we', 'my', 'our'] for token in doc)
        has_experiential_verb = any(token.lemma_.lower() in experiential_verbs for token in doc)
        
        if has_first_person and has_experiential_verb:
            return ClaimType.EXPERIENTIAL
            
        # Modal claims (uncertainty markers)
        if any(re.search(pattern, sentence_lower) for pattern in self.hedging_patterns):
            return ClaimType.MODAL
            
        # Evaluative claims (subjective adjectives)
        evaluative_adjectives = {
            'good', 'bad', 'great', 'terrible', 'amazing', 'awful', 
            'beautiful', 'ugly', 'delicious', 'disgusting', 'wonderful',
            'horrible', 'fantastic', 'boring', 'interesting', 'fun'
        }
        
        if any(token.lemma_.lower() in evaluative_adjectives for token in doc):
            return ClaimType.EVALUATIVE
            
        # Default to factual
        return ClaimType.FACTUAL
    
    def _extract_semantic_components(self, doc) -> Dict[str, str]:
        """Extract subject, predicate, object from dependency parse"""
        components = {}
        
        # Find root verb
        root_verb = None
        for token in doc:
            if token.dep_ == "ROOT":
                root_verb = token
                break
        
        if not root_verb:
            return components
            
        # Extract subject
        for token in doc:
            if token.dep_ in ["nsubj", "nsubjpass"] and token.head == root_verb:
                subject_phrase = self._get_full_phrase(token)
                components['subject'] = subject_phrase
                break
                
        # Extract object
        for token in doc:
            if token.dep_ in ["dobj", "pobj", "attr"] and token.head == root_verb:
                object_phrase = self._get_full_phrase(token)
                components['object'] = object_phrase
                break
                
        # Predicate is the verb + auxiliaries + particles
        predicate_tokens = [root_verb]
        for token in doc:
            if token.head == root_verb and token.dep_ in ["aux", "auxpass", "prt", "neg"]:
                predicate_tokens.append(token)
                
        predicate_tokens.sort(key=lambda x: x.i)
        components['predicate'] = " ".join([t.text for t in predicate_tokens])
        
        return components
    
    def _get_full_phrase(self, head_token):
        """Get the full phrase including modifiers"""
        phrase_tokens = [head_token]
        
        def collect_modifiers(token):
            for child in token.children:
                if child.dep_ in ["det", "amod", "compound", "prep", "pobj", "nummod"]:
                    phrase_tokens.append(child)
                    collect_modifiers(child)
                    
        collect_modifiers(head_token)
        phrase_tokens.sort(key=lambda x: x.i)
        return " ".join([t.text for t in phrase_tokens])
    
    def _extract_modifiers(self, sentence: str, doc) -> Dict:
        """Extract various modifiers that affect claim semantics"""
        modifiers = {}
        sentence_lower = sentence.lower()
        
        # Negation
        modifiers['negated'] = any(
            token.text.lower() in self.negation_markers 
            for token in doc
        )
        
        # Modal strength
        for word, strength in self.modal_expressions.items():
            if word in sentence_lower:
                modifiers['modal'] = strength
                break
        
        # Temporal qualifiers
        for word, qualifier in self.temporal_patterns.items():
            if word in sentence_lower:
                modifiers['temporal'] = qualifier
                break
                
        return modifiers
    
    def _determine_polarity(self, doc, modifiers: Dict) -> ClaimPolarity:
        """Determine if claim is positive, negative, or neutral"""
        
        # Check for explicit negative words
        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate',
            'dislike', 'wrong', 'false', 'untrue', 'impossible', 'never',
            'nothing', 'nobody', 'nowhere', 'fail', 'failure', 'disaster'
        }
        
        positive_words = {
            'good', 'great', 'amazing', 'wonderful', 'fantastic', 'excellent',
            'love', 'like', 'right', 'true', 'correct', 'always', 'perfect',
            'success', 'successful', 'beautiful', 'brilliant'
        }
        
        doc_text_lower = " ".join([token.text.lower() for token in doc])
        
        has_negative = any(word in doc_text_lower for word in negative_words)
        has_positive = any(word in doc_text_lower for word in positive_words)
        
        if modifiers.get('negated', False):
            # Negation flips polarity
            if has_positive:
                return ClaimPolarity.NEGATIVE
            elif has_negative:
                return ClaimPolarity.POSITIVE
                
        if has_positive and not has_negative:
            return ClaimPolarity.POSITIVE
        elif has_negative and not has_positive:
            return ClaimPolarity.NEGATIVE
            
        return ClaimPolarity.NEUTRAL
    
    def _calculate_confidence(self, claim_type: ClaimType, modifiers: Dict) -> float:
        """Calculate confidence score for the claim"""
        base_confidence = {
            ClaimType.FACTUAL: 0.9,
            ClaimType.EXPERIENTIAL: 0.8,
            ClaimType.EVALUATIVE: 0.7,
            ClaimType.PREDICTIVE: 0.6,
            ClaimType.CAUSAL: 0.8,
            ClaimType.COMPARATIVE: 0.8,
            ClaimType.NORMATIVE: 0.7,
            ClaimType.MODAL: 0.5
        }
        
        confidence = base_confidence.get(claim_type, 0.7)
        
        # Adjust based on modifiers
        if modifiers.get('modal') in ['certain', 'likely']:
            confidence *= 1.1
        elif modifiers.get('modal') in ['possible', 'unlikely']:
            confidence *= 0.8
            
        if modifiers.get('temporal') in ['always', 'never']:
            confidence *= 1.1
        elif modifiers.get('temporal') in ['sometimes', 'rarely']:
            confidence *= 0.9
            
        return min(confidence, 1.0)
    
    def _filter_and_enhance_claims(self, claims: List[SemanticClaim]) -> List[SemanticClaim]:
        """Filter out low-quality claims and enhance remaining ones"""
        
        # Remove very low confidence claims
        filtered = [claim for claim in claims if claim.confidence > 0.3]
        
        # Remove duplicates based on semantic hash
        seen_hashes = set()
        unique_claims = []
        
        for claim in filtered:
            if claim.semantic_hash not in seen_hashes:
                seen_hashes.add(claim.semantic_hash)
                unique_claims.append(claim)
                
        # Sort by confidence
        unique_claims.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_claims
    
    def aggregate_claims(self, all_claims: List[SemanticClaim], 
                        user_metadata_list: List[Dict] = None) -> Dict:
        """Aggregate claims for analysis - the key feature for your use case"""
        
        if user_metadata_list is None:
            user_metadata_list = [{} for _ in range(len(all_claims))]
            
        # Group claims by canonical form
        claim_groups = defaultdict(list)
        
        for i, claim in enumerate(all_claims):
            metadata = user_metadata_list[i] if i < len(user_metadata_list) else {}
            claim_groups[claim.canonical_form].append((claim, metadata))
        
        # Create aggregation results
        aggregated = []
        
        for canonical_form, claim_instances in claim_groups.items():
            if len(claim_instances) < 2:  # Skip unique claims
                continue
                
            # Analyze the group
            group_analysis = self._analyze_claim_group(claim_instances)
            aggregated.append(group_analysis)
            
        # Sort by frequency and confidence
        aggregated.sort(key=lambda x: (x['count'], x['avg_confidence']), reverse=True)
        
        return {
            'total_claims': len(all_claims),
            'unique_claims': len(claim_groups),
            'aggregated_claims': aggregated,
            'claim_type_distribution': self._get_type_distribution(all_claims),
            'polarity_distribution': self._get_polarity_distribution(all_claims)
        }
    
    def _analyze_claim_group(self, claim_instances: List[Tuple]) -> Dict:
        """Analyze a group of semantically equivalent claims"""
        claims = [instance[0] for instance in claim_instances]
        metadata_list = [instance[1] for instance in claim_instances]
        
        # Basic stats
        count = len(claims)
        avg_confidence = sum(c.confidence for c in claims) / count
        
        # Most common version
        text_counter = Counter(c.raw_text for c in claims)
        most_common_text = text_counter.most_common(1)[0][0]
        
        # Demographic breakdown if available
        demographic_breakdown = {}
        if metadata_list and any(metadata_list):
            demographic_breakdown = self._analyze_demographics(metadata_list)
        
        return {
            'canonical_form': claims[0].canonical_form,
            'most_common_text': most_common_text,
            'claim_type': claims[0].claim_type.value,
            'polarity': claims[0].polarity.value,
            'count': count,
            'avg_confidence': round(avg_confidence, 3),
            'text_variations': dict(text_counter),
            'demographic_breakdown': demographic_breakdown,
            'semantic_hash': claims[0].semantic_hash
        }
    
    def _analyze_demographics(self, metadata_list: List[Dict]) -> Dict:
        """Analyze demographic distribution of claim supporters"""
        breakdown = {}
        
        # Region analysis
        regions = [m.get('region', 'unknown') for m in metadata_list]
        if any(r != 'unknown' for r in regions):
            breakdown['by_region'] = dict(Counter(regions))
            
        # Age analysis  
        ages = [m.get('age_group', 'unknown') for m in metadata_list]
        if any(a != 'unknown' for a in ages):
            breakdown['by_age'] = dict(Counter(ages))
            
        # Other demographics can be added similarly
        
        return breakdown
    
    def _get_type_distribution(self, claims: List[SemanticClaim]) -> Dict:
        """Get distribution of claim types"""
        type_counts = Counter(claim.claim_type.value for claim in claims)
        return dict(type_counts)
    
    def _get_polarity_distribution(self, claims: List[SemanticClaim]) -> Dict:
        """Get distribution of claim polarities"""
        polarity_counts = Counter(claim.polarity.value for claim in claims)
        return dict(polarity_counts)

# Example usage for your use case
def demo_pulse_analysis():
    """Demonstrate the pulse analysis capability"""
    
    extractor = RobustClaimsExtractor()
    
    # Simulate user posts with metadata
    sample_posts = [
        ("The earth is definitely flat, despite what scientists say", {"region": "US_South", "age_group": "35-44"}),
        ("I think the earth is flat honestly", {"region": "US_South", "age_group": "25-34"}), 
        ("Climate change is completely fake news", {"region": "US_Midwest", "age_group": "45-54"}),
        ("Global warming is not real", {"region": "US_Midwest", "age_group": "55-64"}),
        ("COVID vaccines are dangerous and cause autism", {"region": "US_West", "age_group": "35-44"}),
        ("Vaccines cause autism in children", {"region": "US_West", "age_group": "45-54"}),
        ("The economy is doing great under this administration", {"region": "US_Northeast", "age_group": "25-34"}),
        ("Our economy is thriving right now", {"region": "US_Northeast", "age_group": "35-44"}),
        ("Politicians are all corrupt liars", {"region": "US_South", "age_group": "45-54"}),
        ("All politicians lie and steal from us", {"region": "US_West", "age_group": "35-44"})
    ]

    # Extract claims from all posts
    all_claims = []
    all_metadata = []

    for post_text, metadata in sample_posts:
        claims = extractor.extract_claims(post_text)
        all_claims.extend(claims)
        all_metadata.extend([metadata] * len(claims))

    # Aggregate for pulse analysis
    for claim in all_claims:
        print(claim)
    pulse_analysis = extractor.aggregate_claims(all_claims, all_metadata)

    # Display results
    print("=== REALITY PULSE ANALYSIS ===\n")
    print(f"Total claims processed: {pulse_analysis['total_claims']}")
    print(f"Unique semantic claims: {pulse_analysis['unique_claims']}")

    print(f"\nClaim Type Distribution:")
    for claim_type, count in pulse_analysis['claim_type_distribution'].items():
        print(f"  {claim_type}: {count}")


if __name__ == "__main__":
    demo_pulse_analysis()
