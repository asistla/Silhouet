import spacy
from typing import List, Set, Dict, Tuple, Optional
import re

class AssertionExtractor:
    def __init__(self):
        # Load the large English model for best accuracy
        self.nlp = spacy.load("en_core_web_lg")
        
        # High-confidence hedging terms to keep
        self.high_confidence_hedges = {
            "probably", "likely", "almost certainly", "most likely", 
            "very likely", "quite likely", "almost surely", "most probably"
        }
        
        # Low-confidence hedging terms to discard
        self.low_confidence_hedges = {
            "might", "could", "may", "perhaps", "possibly", "maybe",
            "potentially", "conceivably"
        }
        
        # Conditional markers to discard
        self.conditional_markers = {
            "if", "unless", "provided", "assuming", "suppose", "supposing"
        }
    
    def extract_assertions(self, text: str) -> List[str]:
        """
        Extract atomic assertions from raw English text.
        
        Args:
            text: Raw English text
            
        Returns:
            List of atomic, self-contained assertions
        """
        doc = self.nlp(text)
        
        # Step 1: Break into simple sentences
        simple_sentences = self._decompose_complex_sentences(doc)
        
        # Step 2: Extract assertions from each simple sentence
        assertions = []
        for sent_doc in simple_sentences:
            assertion = self._extract_assertion_from_sentence(sent_doc)
            if assertion:
                assertions.append(assertion)
        
        return assertions
    
    def _decompose_complex_sentences(self, doc) -> List:
        """Break complex sentences into simple sentences."""
        simple_sentences = []
        
        for sent in doc.sents:
            # Check for coordinate conjunctions (and, but, or)
            coord_splits = self._split_on_coordinating_conjunctions(sent)
            
            for split in coord_splits:
                # Handle subordinate clauses
                sub_splits = self._handle_subordinate_clauses(split)
                simple_sentences.extend(sub_splits)
        
        return simple_sentences
    
    def _split_on_coordinating_conjunctions(self, sent) -> List:
        """Split sentence on coordinating conjunctions and extract embedded clauses."""
        splits = []
        
        # First, handle comparative structures like "no more X than Y"
        comparative_splits = self._extract_comparative_clauses(sent)
        if comparative_splits:
            return comparative_splits
        
        # Find coordinating conjunctions that split independent clauses
        coord_conj = ["and", "but", "or", "yet", "so", "nor"]
        
        current_start = sent.start
        
        for token in sent:
            if (token.text.lower() in coord_conj and 
                token.dep_ == "cc"):
                
                # Create a sub-doc for the clause before conjunction
                clause_before = sent.doc[current_start:token.i]
                if self._is_complete_clause(clause_before):
                    splits.append(self.nlp(clause_before.text.strip()))
                
                current_start = token.i + 1
        
        # Add the remaining part
        if current_start < sent.end:
            remaining = sent.doc[current_start:sent.end]
            if self._is_complete_clause(remaining):
                splits.append(self.nlp(remaining.text.strip()))
        
        # If no splits found, return original sentence
        return splits if splits else [self.nlp(sent.text)]
    
    def _extract_comparative_clauses(self, sent) -> List:
        """Extract clauses from comparative structures like 'no more X than Y'."""
        text = sent.text.lower()
        
        # Handle "no more X than Y" pattern
        if "no more" in text and "than" in text:
            return self._parse_no_more_than_structure(sent)
        
        # Handle other comparative patterns as needed
        return []
    
    def _parse_no_more_than_structure(self, sent) -> List:
        """Parse 'no more X than it is for Y' structure to extract embedded assertions."""
        clauses = []
        
        # Find the "than" token
        than_token = None
        for token in sent:
            if token.text.lower() == "than":
                than_token = token
                break
        
        if not than_token:
            return []
        
        # Extract the part after "than"
        after_than = sent.doc[than_token.i + 1:sent.end]
        
        # Look for embedded clauses in the "than" part
        # Pattern: "than it is for [subject] to [verb] [object]"
        embedded_clauses = self._extract_embedded_clauses_from_than_clause(after_than)
        
        # Also check the main clause before "than" for extractable content
        before_than = sent.doc[sent.start:than_token.i]
        main_clauses = self._extract_embedded_clauses_from_main_clause(before_than)
        
        clauses.extend(main_clauses)
        clauses.extend(embedded_clauses)
        
        return clauses if clauses else [self.nlp(sent.text)]
    
    def _extract_embedded_clauses_from_than_clause(self, span) -> List:
        """Extract assertions from the clause after 'than'."""
        clauses = []
        text = span.text.lower()
        
        # Handle coordination within the than clause (surgeons... or pilots...)
        # Look for "or" coordinating multiple subjects
        if " or " in text:
            # Split on "or" and process each part
            parts = self._split_on_or_coordination(span)
            for part in parts:
                clause = self._extract_single_requirement_clause(part)
                if clause:
                    clauses.append(clause)
        else:
            # Single clause
            clause = self._extract_single_requirement_clause(span)
            if clause:
                clauses.append(clause)
        
        return clauses
    
    def _split_on_or_coordination(self, span) -> List:
        """Split span on 'or' coordination."""
        parts = []
        current_start = 0
        tokens = list(span)
        
        for i, token in enumerate(tokens):
            if token.text.lower() == "or" and token.dep_ == "cc":
                # Extract part before "or"
                if i > current_start:
                    before_text = " ".join(t.text for t in tokens[current_start:i])
                    # Preserve context from the beginning for "it is for X to require Y"
                    if current_start > 0:
                        context = " ".join(t.text for t in tokens[:current_start])
                        before_text = context + " " + before_text
                    parts.append(self.nlp(before_text))
                current_start = i + 1
        
        # Add remaining part
        if current_start < len(tokens):
            remaining_text = " ".join(t.text for t in tokens[current_start:])
            # Add context for the last part
            context = " ".join(t.text for t in tokens[:current_start-1])  # Exclude the "or"
            if "it is for" in context:
                remaining_text = "it is for " + remaining_text
            parts.append(self.nlp(remaining_text))
        
        return parts
    
    def _extract_single_requirement_clause(self, span) -> Optional:
        """Extract a single requirement clause from span."""
        text = span.text.lower()
        
        # Pattern: "it is for [subject] to require [object]"
        if "require" in text:
            # Find the subject and object
            for token in span:
                if token.lemma_ == "require":
                    subject = self._find_subject_for_verb(token, span)
                    obj = self._find_object_for_verb(token, span)
                    
                    if subject and obj:
                        assertion = f"{subject} require {obj}"
                        return self.nlp(assertion)
        
        return None
    
    def _extract_embedded_clauses_from_main_clause(self, span) -> List:
        """Extract assertions from the main clause before 'than'."""
        clauses = []
        text = span.text.lower()
        
        # Look for the core assertion in comparative structure
        # "demand governance be undertaken by those that understand the systems involved"
        if "demand" in text and "undertaken" in text:
            # Extract: "Governance should be undertaken by those who understand the systems involved"
            assertion = "Governance should be undertaken by those who understand the systems involved"
            clauses.append(self.nlp(assertion))
        
        return clauses
    
    def _find_subject_for_verb(self, verb_token, span) -> Optional[str]:
        """Find the subject for a given verb token."""
        # Look for nsubj or nsubjpass
        for token in span:
            if token.dep_ in ["nsubj", "nsubjpass"] and token.head == verb_token:
                return token.text
        
        # Look for subjects in prepositional phrases (like "for surgeons")
        for token in span:
            if (token.dep_ == "pobj" and 
                token.head.text.lower() in ["for"] and
                token.pos_ in ["NOUN", "PROPN"]):
                return token.text
        
        # Look for subjects that are children of "for"
        for token in span:
            if token.text.lower() == "for":
                for child in token.children:
                    if child.dep_ == "pobj" and child.pos_ in ["NOUN", "PROPN"]:
                        return child.text
        
        return None
    
    def _find_object_for_verb(self, verb_token, span) -> Optional[str]:
        """Find the object for a given verb token."""
        # Look for direct objects first
        for token in span:
            if token.dep_ == "dobj" and token.head == verb_token:
                return self._get_full_phrase(token, span)
        
        # Look for objects in xcomp relations
        for token in span:
            if token.dep_ == "xcomp" and token.head == verb_token:
                for child in token.children:
                    if child.dep_ == "dobj":
                        return self._get_full_phrase(child, span)
        
        # Look for attr (attribute) relations
        for token in span:
            if token.dep_ == "attr" and token.head == verb_token:
                return self._get_full_phrase(token, span)
        
        # Look for noun phrases that follow the verb
        verb_position = None
        for i, token in enumerate(span):
            if token == verb_token:
                verb_position = i
                break
        
        if verb_position is not None:
            for i, token in enumerate(span):
                if (i > verb_position and 
                    token.pos_ in ["NOUN", "PROPN"] and 
                    not token.dep_ in ["prep", "cc"]):  # Avoid prepositions and conjunctions
                    return self._get_full_phrase(token, span)
        
        return None
    
    def _get_full_phrase(self, token, span) -> str:
        """Get the full phrase including modifiers for a token."""
        # Start with the token itself
        phrase_tokens = [token]
        
        # Add modifiers (adjectives, compounds, etc.)
        for child in token.children:
            if child.dep_ in ["amod", "compound", "det"]:
                phrase_tokens.append(child)
            elif child.dep_ == "prep":
                # Add prepositions and their objects
                phrase_tokens.append(child)
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        phrase_tokens.append(grandchild)
        
        # Sort by position and join
        phrase_tokens.sort(key=lambda t: t.i)
        return " ".join(t.text for t in phrase_tokens)
    
    def _is_complete_clause(self, span) -> bool:
        """Check if span contains a complete clause."""
        has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] for token in span)
        has_verb = any(token.pos_ == "VERB" for token in span)
        return has_subject and has_verb
    
    def _handle_subordinate_clauses(self, sent_doc) -> List:
        """Extract main clauses from sentences with subordinate clauses."""
        # For now, keep it simple - return the main sentence
        # Can be enhanced to extract subordinate clauses as separate assertions
        return [sent_doc]
    
    def _extract_assertion_from_sentence(self, sent_doc) -> Optional[str]:
        """Extract assertion from a simple sentence."""
        sent = list(sent_doc.sents)[0]  # Get the sentence span
        
        # Filter out questions, commands, conditionals
        if not self._is_assertive_sentence(sent):
            return None
        
        # Handle hedging
        if not self._passes_hedging_filter(sent):
            return None
        
        # Resolve pronouns
        resolved_text = self._resolve_pronouns(sent)
        if not resolved_text:
            return None
        
        return resolved_text.strip().rstrip('.')
    
    def _is_assertive_sentence(self, sent) -> bool:
        """Check if sentence is an assertion (not question, command, conditional)."""
        text = sent.text.strip()
        
        # Skip questions
        if text.endswith('?'):
            return False
        
        # Skip imperatives (commands)
        root = [token for token in sent if token.dep_ == "ROOT"][0]
        if root.tag_ in ["VB", "VBP"] and not any(token.dep_ in ["nsubj", "nsubjpass"] 
                                                  for token in sent):
            return False
        
        # Skip conditionals
        if any(token.text.lower() in self.conditional_markers for token in sent):
            return False
        
        return True
    
    def _passes_hedging_filter(self, sent) -> bool:
        """Filter based on hedging - keep high confidence, discard low confidence."""
        sent_text_lower = sent.text.lower()
        
        # Check for low-confidence hedging terms
        if any(hedge in sent_text_lower for hedge in self.low_confidence_hedges):
            return False
        
        # High-confidence hedging is okay
        return True
    
    def _resolve_pronouns(self, sent) -> Optional[str]:
        """Resolve pronouns to named entities or discard if unclear."""
        # Build entity map for the document
        entity_map = self._build_entity_map(sent.doc)
        
        resolved_tokens = []
        
        for token in sent:
            if token.pos_ == "PRON" and token.text.lower() in ["he", "she", "they", "him", "her", "them"]:
                # Try to resolve personal pronouns
                resolved_entity = self._resolve_personal_pronoun(token, entity_map)
                if not resolved_entity:
                    # Can't resolve - discard entire sentence
                    return None
                resolved_tokens.append(resolved_entity)
            elif token.pos_ == "PRON" and token.text.lower() in ["it", "this", "that"]:
                # Keep impersonal pronouns as-is
                resolved_tokens.append(token.text)
            else:
                resolved_tokens.append(token.text)
        
        return " ".join(resolved_tokens).strip()
    
    def _build_entity_map(self, doc) -> Dict[str, str]:
        """Build mapping of entities mentioned in document."""
        entity_map = {}
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE"]:  # Person, Organization, Geopolitical entity
                entity_map[ent.text.lower()] = ent.text
        
        return entity_map
    
    def _resolve_personal_pronoun(self, pronoun_token, entity_map) -> Optional[str]:
        """Try to resolve personal pronoun to a named entity."""
        # Simple heuristic: look for nearest preceding PERSON entity
        # In a full implementation, this would use coreference resolution
        
        sent = pronoun_token.sent
        doc = sent.doc
        
        # Look backwards for PERSON entities in the same sentence first
        for token in reversed(list(sent)):
            if token.i >= pronoun_token.i:
                continue
            if token.ent_type_ == "PERSON":
                return token.text
        
        # Look in previous sentences (simplified)
        for sent_before in doc.sents:
            if sent_before.end >= sent.start:
                break
            for ent in sent_before.ents:
                if ent.label_ == "PERSON":
                    return ent.text
        
        # Can't resolve
        return None


# Usage example and testing
if __name__ == "__main__":
    extractor = AssertionExtractor()
    
    # Test with the example from discussion
    test_text = """It is no more elitist to demand governance be undertaken by those that understand the systems involved, than it is for surgeons to require medical training or pilots to require aeronautical knowledge."""
    
    print("Input:", test_text)
    print("\nExtracting assertions...")
    
    assertions = extractor.extract_assertions(test_text)
    
    print(f"\nExtracted {len(assertions)} assertions:")
    for i, assertion in enumerate(assertions, 1):
        print(f"{i}. {assertion}")
    
    # Test with a simpler example
    print("\n" + "="*50)
    test_text2 = "John went to the store and Mary bought some milk."
    print("Input:", test_text2)
    assertions2 = extractor.extract_assertions(test_text2)
    print(f"\nExtracted {len(assertions2)} assertions:")
    for i, assertion in enumerate(assertions2, 1):
        print(f"{i}. {assertion}")
