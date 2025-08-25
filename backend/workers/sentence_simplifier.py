# pip install spacy
# python -m spacy download en_core_web_sm
import spacy
from typing import List, Tuple, Set

CLAUSE_DEPS = {"ROOT", "conj", "advcl", "ccomp", "xcomp", "relcl"}
SUBJ_DEPS = {"nsubj", "nsubjpass", "expl"}  # expl handles "there is/are"
OBJ_LIKE = {"obj", "dobj", "pobj", "attr", "oprd"}
NEG_DEPS = {"neg"}
REL_PRONOUNS = {"who", "whom", "whose", "which", "that"}

class SentenceSimplifier:
    def __init__(self, nlp):
        self.nlp = nlp

    def simplify(self, text: str) -> List[str]:
        doc = self.nlp(text)
        out: List[str] = []
        for sent in doc.sents:
            out.extend(self._simplify_sentence(sent))
        # dedupe while preserving order
        seen: Set[str] = set()
        uniq = []
        for s in out:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        del seen
        return uniq

    # ---------------- internal helpers ----------------

    def _simplify_sentence(self, sent: spacy.tokens.Span) -> List[str]:
        
        def get_full_subtree(token: spacy.tokens.Token) -> List[spacy.tokens.Token]:
            """Gets the token and all its children in a flat list."""
            return list(token.subtree)

        def find_subject(verb: spacy.tokens.Token) -> spacy.tokens.Token | None:
            for child in verb.children:
                if child.dep_ in SUBJ_DEPS:
                    return child
            # Check ancestors for inherited subject (e.g., in coordinated clauses)
            for ancestor in verb.ancestors:
                # In cases of xcomp, the subject is often the subject of the parent verb
                if ancestor.pos_ == 'VERB':
                    for child in ancestor.children:
                        if child.dep_ in SUBJ_DEPS:
                            return child
            return None

        def build_clause(verb: spacy.tokens.Token) -> str | None:
            subject = find_subject(verb)
            if not subject:
                return None # Can't form a meaningful claim without a subject

            clause_parts = []
            # Add subject and its full phrase
            clause_parts.extend(get_full_subtree(subject))
            
            # Add verb and its auxiliaries/negations
            clause_parts.append(verb)
            for child in verb.children:
                if child.dep_ in ('aux', 'auxpass', 'neg'):
                    clause_parts.append(child)

            # Add objects, complements, and key prepositional phrases
            for child in verb.children:
                if child.dep_ in OBJ_LIKE or child.dep_ in ('acomp', 'prep', 'advcl', 'ccomp'):
                    clause_parts.extend(get_full_subtree(child))
            
            # Sort tokens by their original position in the sentence
            clause_parts = sorted(list(set(clause_parts)), key=lambda t: t.i)
            
            # Filter out subordinate conjunctions at the start
            if clause_parts and clause_parts[0].dep_ == 'mark':
                clause_parts = clause_parts[1:]

            text = ' '.join(t.text for t in clause_parts)
            return self._clean_cap(self._strip_punct(text))

        clauses = []
        # Find all verbs that could be the root of a clause
        for token in sent:
            if token.pos_ == 'VERB' and token.dep_ in CLAUSE_DEPS:
                clause = build_clause(token)
                if clause and len(clause.split()) > 3: # Basic quality filter
                    clauses.append(clause)

        if not clauses:
            return [self._clean_cap(self._strip_punct(sent.text))]

        return clauses

    def _stable_order(self, toks: List[spacy.tokens.Token]) -> List[spacy.tokens.Token]:
        # deterministic left-to-right
        return sorted(toks, key=lambda t: t.i)

    def _find_subject(self, root: spacy.tokens.Token) -> str | None:
        # direct subject under this root
        for child in root.children:
            if child.dep_ in SUBJ_DEPS:
                return self._span_text_for_subject(child)
        # subject may be raised from ancestors (e.g., for conj)
        head = root.head
        while head is not None and head.dep_ != "ROOT" and head != root:
            for child in head.children:
                if child.dep_ in SUBJ_DEPS:
                    return self._span_text_for_subject(child)
            head = head.head
        return None

    def _inherit_subject(self, root: spacy.tokens.Token, inherited: str | None) -> str | None:
        # coordination: inherit from head clause
        if root.dep_ == "conj":
            # try head's subject first
            subj = self._find_subject(root.head)
            if subj:
                return subj
        return inherited

    def _span_text_for_subject(self, subj_tok: spacy.tokens.Token) -> str:
        # use noun chunk if available, else subtree
        sent = subj_tok.doc[subj_tok.sent.start:subj_tok.sent.end]
        for chunk in sent.noun_chunks:
            if subj_tok.i in range(chunk.start, chunk.end):
                return chunk.text
        return subj_tok.subtree.text

    def _assemble_clause(self, sent: spacy.tokens.Span, root: spacy.tokens.Token, subject_text: str | None) -> str | None:
        """
        Build a readable simple sentence:
          [Subject] + [aux/neg/root/objects/necessary modifiers]
        Excludes nested clause subtrees belonging to other clause roots to avoid duplication.
        """
        # Tokens to exclude: subtrees of other clause roots (except current root)
        excluded_idxs = set()

        # Collect pieces around the root
        aux = [t for t in root.children if t.dep_ in {"aux", "auxpass"} and t.i not in excluded_idxs]
        neg = [t for t in root.children if t.dep_ in NEG_DEPS and t.i not in excluded_idxs]
        objs = [t for t in root.children if (t.dep_.endswith("obj") or t.dep_ in OBJ_LIKE) and t.i not in excluded_idxs]
        comps = [t for t in root.children if t.dep_ in {"acomp", "attr", "oprd"} and t.i not in excluded_idxs]
        admods = [t for t in root.children if t.dep_ in {"advmod", "npadvmod"} and t.i not in excluded_idxs]
        prep_phrases = [t for t in root.children if t.dep_ == "prep" and t.i not in excluded_idxs]

        # Subject
        subj_txt = subject_text
        if subj_txt is None:
            # expletive constructions: "There is/are ..."
            if any(t.lower_ == "there" and t.dep_ == "expl" for t in root.children):
                subj_txt = "There"
            else:
                # try last noun chunk before the root
                subj_txt = self._closest_left_noun_chunk(sent, root)

        # Build string
        parts: List[str] = []
        if subj_txt:
            parts.append(subj_txt)

        # auxiliaries (sorted by position)
        parts.extend([t.text for t in sorted(aux, key=lambda x: x.i)])
        # negation
        parts.extend([t.text for t in sorted(neg, key=lambda x: x.i)])

        # main verb/copula
        verb_form = root.text
        # normalize comparative wrappers like "is" inside "as ... as", leave as-is otherwise
        parts.append(verb_form)

        # predicate complements / objects / modifiers in textual order
        def span_text(tokens: List[spacy.tokens.Token]) -> List[str]:
            if not tokens: return []
            toks = []
            for t in sorted(tokens, key=lambda x: x.i):
                toks += [x.text for x in t.subtree]
            return toks

        parts.extend(span_text(comps))
        parts.extend(span_text(objs))
        parts.extend(span_text(admods))
        parts.extend(span_text(prep_phrases))

        # Clean and finalize
        clause = " ".join(parts).strip()
        if not clause:
            return None
        clause = self._strip_punct(clause)
        if not clause.endswith("."):
            clause += "."
        return clause

    def _closest_left_noun_chunk(self, sent: spacy.tokens.Span, root: spacy.tokens.Token) -> str | None:
        candidate = None
        for chunk in sent.noun_chunks:
            if chunk.end <= root.i:
                candidate = chunk
        return candidate.text if candidate else None

    @staticmethod
    def _strip_punct(s: str) -> str:
        return s.strip().strip(" ,;:!?\u0964\u0965")

    @staticmethod
    def _clean_cap(s: str) -> str:
        s = " ".join(s.split())  # collapse whitespace
        return s[0].upper() + s[1:] if s else s

