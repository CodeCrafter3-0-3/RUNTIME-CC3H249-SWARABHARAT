"""
Lightweight embeddings and similarity search using bag-of-words + numpy.
This is intentionally simple to avoid heavy dependencies and to provide
an on-disk, no-external-service fallback for semantic search.
"""
from typing import List, Dict, Tuple
import re
import numpy as np

def _tokenize(text: str):
    text = (text or '').lower()
    tokens = re.findall(r"\b\w+\b", text)
    return tokens

def _build_vocab(reports: List[Dict]):
    vocab = {}
    for r in reports:
        tokens = _tokenize(r.get('message') or r.get('summary') or '')
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
    return vocab

def _vectorize(text: str, vocab: Dict[str,int]):
    vec = np.zeros(len(vocab), dtype=float)
    for t in _tokenize(text):
        idx = vocab.get(t)
        if idx is not None:
            vec[idx] += 1.0
    # normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

def build_vectors(reports: List[Dict]):
    vocab = _build_vocab(reports)
    vectors = []
    for r in reports:
        text = (r.get('message') or r.get('summary') or '')
        vectors.append(_vectorize(text, vocab))
    if vectors:
        matrix = np.vstack(vectors)
    else:
        matrix = np.zeros((0, len(vocab)))
    return vocab, matrix


def find_similar(query: str, reports: List[Dict], top_n: int = 5) -> List[Dict]:
    """Return top_n similar reports to the query with cosine scores."""
    if not query or not reports:
        return []
    vocab, matrix = build_vectors(reports)
    qv = _vectorize(query, vocab)
    if matrix.size == 0:
        return []
    # cosine similarity
    scores = (matrix @ qv)
    # get top indices
    idxs = np.argsort(-scores)[:top_n]
    results = []
    for i in idxs:
        score = float(scores[i])
        r = reports[i].copy()
        # include a snippet and score
        snippet = (r.get('summary') or r.get('message') or '')[:300]
        results.append({'id': r.get('id'), 'score': round(score, 4), 'snippet': snippet, 'report': r})
    return results
