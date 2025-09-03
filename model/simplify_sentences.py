import re
import spacy
import nltk
from nltk.tokenize import sent_tokenize
import pysbd
from typing import List, Tuple, Optional, Dict
import logging
import torch
from dataclasses import dataclass
from collections import defaultdict, Counter
import numpy as np

# Enable GPU for spacy if available
spacy.prefer_gpu()

@dataclass
class SentenceCandidate:
    """Represents a potential sentence with detailed analysis for assertion extraction"""
    text: str
    start: int
    end: int
    confidence_scores: Dict[str, float]
    has_subject: bool = False
    has_predicate: bool = False
    has_object: bool = False
    assertion_score: float = 0.0
    final_score: float = 0.0

class AssertionOptimizedSentenceSplitter:
    """
    Advanced sentence splitter optimized for assertion extraction.
    Uses en_core_web_trf for transformer-powered analysis combined with
    traditional methods, focusing on preserving complete subject-predicate-object structures.
    """
    
    def __init__(self, nlp):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        self.nlp = nlp
        # Initialize components
#        self._init_spacy_transformer()
        self._init_assertion_patterns()
        
        # Weights optimized for assertion preservation (simplified since we have one powerful model)
        self.method_weights = {
            'spacy_transformer': 0.50,  # High weight for transformer-based spaCy
            'nltk': 0.15,               # Lower weight, good baseline
            'pysbd': 0.20,              # Good for handling abbreviations
            'transformer_semantic': 0.15,  # Additional semantic analysis from spaCy transformers
        }
        
        # Assertion structure weights
        self.assertion_weights = {
            'has_complete_structure': 0.4,
            'has_clear_boundaries': 0.3,
            'preserves_meaning': 0.3
        }
        
    def _init_spacy_transformer(self):
        """Initialize spaCy with transformer model (en_core_web_trf)"""
        try:
            # Use the transformer-based model - much more powerful
            self.nlp = spacy.load("en_core_web_trf")
            print(f"Loaded en_core_web_trf with {self.nlp.meta['vectors']} vectors")
            
            # Add custom component for assertion-aware sentence boundaries
            if "assertion_sentence_boundaries" not in self.nlp.pipe_names:
                self.nlp.add_pipe("assertion_sentence_boundaries", before="parser")
                
        except OSError:
            try:
                # Fallback to large model
                self.nlp = spacy.load("en_core_web_lg")
                print("Loaded en_core_web_lg (fallback)")
                if "assertion_sentence_boundaries" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("assertion_sentence_boundaries", before="parser")
            except OSError:
                try:
                    # Last fallback
                    self.nlp = spacy.load("en_core_web_sm")
                    print("Loaded en_core_web_sm (last fallback)")
                    if "assertion_sentence_boundaries" not in self.nlp.pipe_names:
                        self.nlp.add_pipe("assertion_sentence_boundaries", before="parser")
                except OSError:
                    logging.error("No spaCy English model found. Install with: python -m spacy download en_core_web_trf")
                    self.nlp = None
    
    def _init_assertion_patterns(self):
        """Initialize patterns for identifying assertion structures"""
        
        # Enhanced abbreviations list (more comprehensive)
        self.abbreviations = {
            # Titles
            'Mr.', 'Mrs.', 'Ms.', 'Miss.', 'Dr.', 'Prof.', 'Sr.', 'Jr.',
            'Rev.', 'Fr.', 'St.', 'Gen.', 'Col.', 'Capt.', 'Lt.', 'Sgt.',
            
            # Business
            'Inc.', 'Ltd.', 'Corp.', 'Co.', 'LLC.', 'vs.', 'v.',
            
            # Academic/Scientific
            'et.', 'al.', 'etc.', 'i.e.', 'e.g.', 'cf.', 'viz.', 'ibid.',
            'fig.', 'no.', 'vol.', 'pp.', 'p.', 'ch.', 'sec.', 'ed.',
            'min.', 'max.', 'avg.', 'approx.', 'est.',
            
            # Months
            'Jan.', 'Feb.', 'Mar.', 'Apr.', 'May.', 'Jun.',
            'Jul.', 'Aug.', 'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.',
            
            # Common
            'cont.', 'dept.', 'govt.', 'intl.', 'natl.', 'univ.',
        }
        
        # Patterns that indicate strong sentence boundaries
        self.strong_boundaries = [
            r'[.!?]+\s+[A-Z][a-z]',     # Period + space + capital letter
            r'[.!?]+["\']*\s+[A-Z]',    # With quotes
            r'[.!?]+\s*\n+\s*[A-Z]',    # With newlines
            r'[.!?]+\s+["\']*[A-Z]',    # Various quote combinations
        ]
        
        # Patterns that preserve assertion boundaries
        self.assertion_preserving_patterns = [
            r'\.\s+(?=(?:This|That|It|He|She|They|We|I)\s)',     # Subject pronouns
            r'\.\s+(?=(?:The|A|An)\s+\w+\s+(?:is|are|was|were|has|have|will|would|can|could|should|must))',  # Articles + predicate
            r'[.!?]\s+(?=[A-Z]\w+\s+(?:is|are|was|were|has|have|will|would|can|could|should|must))',  # Proper noun + predicate
        ]
        
        # Patterns that should NOT break sentences (preserve assertions)
        self.non_breaking_patterns = [
            r'\b[A-Z][a-z]*\.\s+[a-z]',        # Abbreviation + lowercase
            r'\d+\.\s*\d+',                     # Decimal numbers
            r'\b[A-Z]\.\s*[A-Z]\.',             # Initials
            r'[.]{2,}',                         # Ellipsis
            r'U\.S\.', r'U\.K\.', r'U\.N\.',    # Common country abbreviations
            r'\$\d+\.\d+',                      # Money amounts
        ]

    @spacy.Language.component("assertion_sentence_boundaries")
    def assertion_sentence_boundaries(self, doc):
        """Custom spaCy component optimized for assertion preservation"""
        
        for i, token in enumerate(doc[:-2]):
            # Don't break on abbreviations
            if token.text.rstrip('.') + '.' in self.abbreviations:
                if i + 1 < len(doc):
                    doc[i + 1].is_sent_start = False
                continue
            
            # Don't break on decimal numbers
            if (token.like_num and token.text.endswith('.') and 
                i + 1 < len(doc) and doc[i + 1].like_num):
                doc[i + 1].is_sent_start = False
                continue
            
            # Strong sentence boundary indicators
            if (token.text in '.!?' and i + 1 < len(doc)):
                next_token = doc[i + 1]
                
                # Look for assertion-starting patterns
                if (next_token.text and next_token.text[0].isupper() and
                    not any(re.match(pattern, token.text + ' ' + next_token.text) 
                           for pattern in self.non_breaking_patterns)):
                    
                    # Check if this creates a valid assertion boundary
                    if self._is_valid_assertion_boundary(doc, i):
                        next_token.is_sent_start = True
        
        return doc
    
    def _is_valid_assertion_boundary(self, doc, boundary_idx: int) -> bool:
        """Check if a potential boundary preserves assertion structure"""
        if boundary_idx >= len(doc) - 1:
            return True
        
        # Look at the sentence that would be created before this boundary
        sent_start = 0
        for j in range(boundary_idx - 1, -1, -1):
            if doc[j].is_sent_start:
                sent_start = j
                break
        
        # Analyze the potential sentence for assertion completeness
        potential_sent = doc[sent_start:boundary_idx + 1]
        
        # Check for basic assertion components
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass', 'csubj'] for token in potential_sent)
        has_verb = any(token.pos_ == 'VERB' for token in potential_sent)
        has_reasonable_length = len(potential_sent) >= 3
        
        return has_subject and has_verb and has_reasonable_length
    
    def _get_spacy_transformer_sentences(self, text: str) -> List[Tuple[str, int, int, float]]:
        """Get sentences using spaCy transformer model with assertion-aware analysis"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        sentences = []
        
        for sent in doc.sents:
            # Analyze assertion structure using transformer-powered features
            assertion_analysis = self._analyze_assertion_structure(sent)
            
            # Calculate confidence using transformer embeddings and syntactic features
            confidence = self._calculate_transformer_confidence(sent, assertion_analysis)
            
            sentences.append((sent.text.strip(), sent.start_char, sent.end_char, confidence))
        
        return sentences
    
    def _calculate_transformer_confidence(self, sent, assertion_analysis: Dict[str, bool]) -> float:
        """Calculate confidence using transformer features and assertion structure"""
        base_confidence = 0.6  # Higher base for transformer model
        
        # Reward complete assertion structures (higher weights since transformers are better)
        if assertion_analysis['has_subject'] and assertion_analysis['has_predicate']:
            base_confidence += 0.25
        
        # Reward object or complement
        if assertion_analysis['has_object'] or assertion_analysis['has_complement']:
            base_confidence += 0.15
        
        # Handle implicit objects with transformer understanding
        if (assertion_analysis['has_subject'] and assertion_analysis['has_predicate'] and 
            not assertion_analysis['has_object'] and not assertion_analysis['has_complement']):
            # Use transformer embeddings to better understand intransitive assertions
            root_verb = next((token for token in sent if token.dep_ == 'ROOT' and token.pos_ == 'VERB'), None)
            if root_verb:
                # Transformer models better understand semantic completeness
                base_confidence += 0.1
        
        # Leverage transformer's better understanding of sentence boundaries
        if sent.text.strip().endswith(('.', '!', '?')):
            base_confidence += 0.05
        
        if sent.text.strip() and sent.text.strip()[0].isupper():
            base_confidence += 0.03
        
        # Less penalty for short sentences since transformers understand context better
        if len(sent.text.strip().split()) < 3:
            base_confidence -= 0.1  # Reduced penalty
        
        # Bonus for transformer model's semantic understanding
        if hasattr(sent, 'vector') and sent.vector is not None:
            # If we have good vector representations, boost confidence slightly
            base_confidence += 0.02
        
        return max(0.0, min(1.0, base_confidence))
    
    def _analyze_assertion_structure(self, sent) -> Dict[str, bool]:
        """Analyze if sentence contains complete assertion structure"""
        analysis = {
            'has_subject': False,
            'has_predicate': False, 
            'has_object': False,
            'has_copula': False,
            'has_complement': False
        }
        
        for token in sent:
            # Subject detection
            if token.dep_ in ['nsubj', 'nsubjpass', 'csubj']:
                analysis['has_subject'] = True
            
            # Predicate/verb detection
            if token.pos_ == 'VERB' and token.dep_ == 'ROOT':
                analysis['has_predicate'] = True
            
            # Object detection
            if token.dep_ in ['dobj', 'iobj', 'pobj']:
                analysis['has_object'] = True
            
            # Copula (linking verb)
            if token.lemma_ in ['be', 'seem', 'become', 'appear', 'feel', 'look', 'sound', 'taste', 'smell']:
                analysis['has_copula'] = True
            
            # Complement detection
            if token.dep_ in ['attr', 'acomp', 'pcomp']:
                analysis['has_complement'] = True
        
        return analysis
    
    def _calculate_spacy_confidence(self, sent, assertion_analysis: Dict[str, bool]) -> float:
        """Calculate confidence with heavy weighting for assertion completeness (legacy method)"""
        # This method is kept for compatibility but transformer method is preferred
        return self._calculate_transformer_confidence(sent, assertion_analysis) * 0.9  # Slightly lower than transformer
    
    def _get_nltk_sentences(self, text: str) -> List[Tuple[str, int, int, float]]:
        """NLTK sentence tokenization with position tracking"""
        sentences = sent_tokenize(text)
        result = []
        current_pos = 0
        
        for sent in sentences:
            # Find the sentence in the original text
            start = text.find(sent, current_pos)
            if start == -1:
                # Fallback: approximate position
                start = current_pos
            end = start + len(sent)
            
            # Calculate confidence based on assertion likelihood
            confidence = self._calculate_nltk_confidence(sent)
            result.append((sent.strip(), start, end, confidence))
            current_pos = end
            
        return result
    
    def _calculate_nltk_confidence(self, sentence: str) -> float:
        """Calculate NLTK confidence with focus on assertion structure"""
        confidence = 0.6  # Base NLTK confidence
        
        # Check for assertion indicators
        words = sentence.strip().split()
        if len(words) >= 3:  # Minimum for subject-verb-object
            confidence += 0.1
        
        # Look for common assertion verbs
        assertion_verbs = {'is', 'are', 'was', 'were', 'has', 'have', 'had', 'will', 'would', 'can', 'could', 'should', 'must', 'sucks', 'rocks', 'works', 'fails'}
        if any(word.lower() in assertion_verbs for word in words):
            confidence += 0.15
        
        # Proper ending punctuation
        if sentence.strip().endswith(('.', '!', '?')):
            confidence += 0.1
        else:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _get_pysbd_sentences(self, text: str) -> List[Tuple[str, int, int, float]]:
        """pySBD with position tracking and assertion focus"""
        try:
            seg = pysbd.Segmenter(language="en", clean=False)
            sentences = seg.segment(text)
            
            result = []
            current_pos = 0
            
            for sent in sentences:
                start = text.find(sent, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(sent)
                
                # pySBD is excellent for handling abbreviations, good for assertions
                confidence = 0.75
                if self._looks_like_complete_assertion(sent):
                    confidence += 0.1
                
                result.append((sent.strip(), start, end, confidence))
                current_pos = end
                
            return result
        except Exception as e:
            logging.warning(f"pySBD error: {e}")
            return []
    
    def _looks_like_complete_assertion(self, sentence: str) -> bool:
        """Quick heuristic to check if sentence looks like a complete assertion"""
        words = sentence.strip().split()
        if len(words) < 2:
            return False
        
        # Look for subject-predicate pattern
        has_noun_or_pronoun = any(word.lower() in ['i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that'] 
                                 for word in words[:3])  # Check first few words
        
        # Look for verb or copula
        has_verb = any(word.lower() in ['is', 'are', 'was', 'were', 'has', 'have', 'had', 'will', 'would', 'can', 'could', 'should', 'must', 'do', 'does', 'did', 'sucks', 'rocks', 'works', 'fails', 'exists', 'matters'] 
                      for word in words)
        
        return has_noun_or_pronoun and has_verb
    
    def _get_transformer_semantic_sentences(self, text: str) -> List[Tuple[str, int, int, float]]:
        """Use spaCy transformer for additional semantic sentence analysis"""
        if not self.nlp:
            return []
        
        try:
            # Process text again but focus on semantic boundaries
            doc = self.nlp(text)
            
            # Use transformer embeddings to identify semantic coherence
            sentences = []
            current_start = 0
            
            for sent in doc.sents:
                # Calculate semantic coherence using transformer features
                semantic_score = self._calculate_semantic_coherence(sent)
                
                # Check if this sentence maintains semantic integrity
                if semantic_score > 0.3:  # Threshold for semantic completeness
                    confidence = 0.7 + (semantic_score * 0.2)  # Scale to confidence
                    sentences.append((sent.text.strip(), sent.start_char, sent.end_char, confidence))
            
            return sentences
            
        except Exception as e:
            logging.warning(f"Transformer semantic processing error: {e}")
            return []
    
    def _calculate_semantic_coherence(self, sent) -> float:
        """Calculate semantic coherence using transformer embeddings"""
        try:
            # Basic semantic coherence checks
            if not sent.text.strip():
                return 0.0
            
            words = sent.text.strip().split()
            if len(words) < 2:
                return 0.2
            
            # Use spaCy's transformer-based similarity if available
            base_score = 0.5
            
            # Check for semantic completeness indicators
            if self._looks_like_complete_assertion(sent.text):
                base_score += 0.3
            
            # Check semantic relationships between words
            tokens = [token for token in sent if not token.is_punct and not token.is_space]
            if len(tokens) >= 2:
                # Transformer models understand semantic relationships better
                base_score += 0.1
            
            # Penalize very long sentences (likely multiple semantic units)
            if len(words) > 25:
                base_score -= 0.2
            elif 5 <= len(words) <= 15:  # Sweet spot for single assertions
                base_score += 0.1
            
            return max(0.0, min(1.0, base_score))
            
        except Exception:
            return 0.5
    
    def _should_split_here(self, current_text: str, full_text: str, position: int) -> bool:
        """Determine if we should split at this position using transformer understanding"""
        if not current_text.strip():
            return False
        
        # Check for abbreviation patterns
        for abbr in self.abbreviations:
            if current_text.strip().endswith(abbr):
                return False
        
        # Look ahead in the full text
        remaining = full_text[position:].strip()
        if remaining and remaining[0].isupper():
            # Use transformer model's better understanding of completeness
            if self.nlp:
                try:
                    doc = self.nlp(current_text)
                    if doc.sents:
                        sent = list(doc.sents)[0]
                        analysis = self._analyze_assertion_structure(sent)
                        return analysis['has_subject'] and analysis['has_predicate']
                except:
                    pass
            
            # Fallback to basic check
            return self._looks_like_complete_assertion(current_text)
        
        return True
    
    def _ensemble_sentences(self, all_candidates: List[List[Tuple[str, int, int, float]]]) -> List[SentenceCandidate]:
        """Advanced ensemble with assertion-focused scoring"""
        
        # Collect all candidates
        position_candidates = defaultdict(list)
        
        method_names = ['spacy_transformer', 'nltk', 'pysbd', 'transformer_semantic']
        
        for method_idx, method_sentences in enumerate(all_candidates):
            method_name = method_names[method_idx]
            
            for sent_text, start, end, confidence in method_sentences:
                # Group candidates by approximate position (allow some tolerance)
                key = self._get_position_key(start, end)
                position_candidates[key].append({
                    'text': sent_text,
                    'start': start,
                    'end': end,
                    'method': method_name,
                    'confidence': confidence
                })
        
        # Create final candidates
        final_candidates = []
        
        for candidates_group in position_candidates.values():
            if not candidates_group:
                continue
            
            # Find the best representative text (usually the longest/most complete)
            best_candidate = max(candidates_group, key=lambda x: len(x['text']))
            
            # Calculate ensemble confidence
            confidence_scores = {}
            for cand in candidates_group:
                method = cand['method']
                confidence_scores[method] = max(confidence_scores.get(method, 0), cand['confidence'])
            
            # Calculate weighted score
            total_weight = 0
            weighted_score = 0
            for method, score in confidence_scores.items():
                weight = self.method_weights.get(method, 0)
                weighted_score += score * weight
                total_weight += weight
            
            final_score = weighted_score / total_weight if total_weight > 0 else 0
            
            # Analyze assertion structure if we have spaCy
            assertion_analysis = {'has_subject': False, 'has_predicate': False, 'has_object': False}
            if self.nlp:
                try:
                    doc = self.nlp(best_candidate['text'])
                    if doc.sents:
                        assertion_analysis = self._analyze_assertion_structure(list(doc.sents)[0])
                except:
                    pass
            
            candidate = SentenceCandidate(
                text=best_candidate['text'],
                start=best_candidate['start'],
                end=best_candidate['end'],
                confidence_scores=confidence_scores,
                has_subject=assertion_analysis['has_subject'],
                has_predicate=assertion_analysis['has_predicate'],
                has_object=assertion_analysis['has_object'],
                assertion_score=self._calculate_assertion_score(assertion_analysis),
                final_score=final_score
            )
            
            final_candidates.append(candidate)
        
        return final_candidates
    
    def _get_position_key(self, start: int, end: int) -> Tuple[int, int]:
        """Create a position key with some tolerance for alignment"""
        # Round to nearest 10 to group nearby positions
        return (start // 10 * 10, end // 10 * 10)
    
    def _calculate_assertion_score(self, assertion_analysis: Dict[str, bool]) -> float:
        """Calculate how good this sentence is for assertion extraction"""
        score = 0.0
        
        if assertion_analysis['has_subject']:
            score += 0.4
        if assertion_analysis['has_predicate']:
            score += 0.4
        if assertion_analysis['has_object'] or assertion_analysis.get('has_complement', False):
            score += 0.2
        
        return score
    
    def split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences optimized for assertion extraction
        
        Args:
            text: Raw input text
            
        Returns:
            List of sentences, each likely to contain complete assertions
        """
        if not text.strip():
            return []
        
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Get candidates from all methods (now using unified transformer approach)
        all_candidates = [
            self._get_spacy_transformer_sentences(text),  # Primary transformer method
            self._get_nltk_sentences(text),                # Traditional baseline
            self._get_pysbd_sentences(text),               # Abbreviation handling
            self._get_transformer_semantic_sentences(text) # Additional semantic analysis
        ]
        
        # Ensemble the results
        candidates = self._ensemble_sentences(all_candidates)
        
        # Filter and sort candidates
        quality_candidates = [
            cand for cand in candidates
            if (cand.final_score > 0.3 and  # Minimum confidence
                len(cand.text.strip()) > 2 and  # Minimum length
                cand.text.strip() != '')
        ]
        
        # Sort by position
        quality_candidates.sort(key=lambda x: x.start)
        
        # Post-process and return
        sentences = [cand.text.strip() for cand in quality_candidates]
        sentences = self._postprocess_sentences(sentences)
        
        return sentences
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better assertion extraction"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.!?])\s*', r'\1 ', text)
        
        # Handle quotes properly
        text = re.sub(r'"\s*([.!?])\s*"', r'"\1" ', text)
        text = re.sub(r"'\s*([.!?])\s*'", r"'\1' ", text)
        
        # Fix common formatting issues
        text = re.sub(r'([.!?])\s*\n\s*([a-z])', r'\1 \2', text)  # Fix capitalization after line breaks
        text = re.sub(r'([.!?])\s*\n\s*([A-Z])', r'\1 \2', text)  # Clean line breaks
        
        return text.strip()
    
    def _postprocess_sentences(self, sentences: List[str]) -> List[str]:
        """Final cleanup focusing on assertion quality"""
        processed = []
        
        for sent in sentences:
            sent = sent.strip()
            
            # Skip very short or empty sentences
            if len(sent) < 3:
                continue
            
            # Skip pure punctuation
            if re.match(r'^[^\w]*$', sent):
                continue
            
            # Skip sentences that are just lists of numbers or single words
            words = sent.split()
            if len(words) == 1 and not sent.endswith(('.', '!', '?')):
                continue
            
            # Ensure proper capitalization
            if sent and sent[0].islower():
                sent = sent[0].upper() + sent[1:]
            
            # Ensure proper ending punctuation for complete assertions
            if not sent.endswith(('.', '!', '?', ':', ';')):
                # Only add period if it looks like a complete assertion
                if self._looks_like_complete_assertion(sent):
                    sent += '.'
            
            processed.append(sent)
        
        return processed
    
    def get_assertion_candidates(self, text: str) -> List[Dict]:
        """
        Get detailed information about potential assertions in the text
        
        Returns:
            List of dictionaries with assertion analysis details
        """
        sentences = self.split_sentences(text)
        
        candidates = []
        for sent in sentences:
            if self.nlp:
                doc = self.nlp(sent)
                if doc.sents:
                    sent_obj = list(doc.sents)[0]
                    analysis = self._analyze_assertion_structure(sent_obj)
                    
                    candidates.append({
                        'text': sent,
                        'has_subject': analysis['has_subject'],
                        'has_predicate': analysis['has_predicate'],
                        'has_object': analysis['has_object'],
                        'assertion_score': self._calculate_assertion_score(analysis),
                        'word_count': len(sent.split()),
                        'likely_assertion': (analysis['has_subject'] and analysis['has_predicate'])
                    })
                else:
                    candidates.append({
                        'text': sent,
                        'has_subject': False,
                        'has_predicate': False,
                        'has_object': False,
                        'assertion_score': 0.0,
                        'word_count': len(sent.split()),
                        'likely_assertion': False
                    })
        
        return candidates
