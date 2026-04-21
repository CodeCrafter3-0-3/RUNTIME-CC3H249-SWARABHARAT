import os
import json
from typing import List, Tuple, Dict
from pathlib import Path
import numpy as np
from datetime import datetime, timezone

from embeddings import build_vectors, _vectorize

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# If REPORTS_FILE env var is set (tests or deployments), place embeddings
# next to that file so tests using tmp REPORTS_FILE don't pollute repository folders.
import os as _os
REPORTS_FILE_ENV = _os.environ.get('REPORTS_FILE')
if REPORTS_FILE_ENV:
    EMB_DIR = _os.path.join(_os.path.dirname(REPORTS_FILE_ENV), 'embeddings')
else:
    EMB_DIR = os.path.join(DATA_DIR, 'embeddings')

os.makedirs(EMB_DIR, exist_ok=True)

VOCAB_FILE = os.path.join(EMB_DIR, 'vocab.json')
MATRIX_FILE = os.path.join(EMB_DIR, 'matrix.npz')
IDS_FILE = os.path.join(EMB_DIR, 'ids.json')


def build_and_save_index(reports: List[Dict]) -> Dict:
    """Build embeddings for reports and persist them to disk."""
    vocab, matrix = build_vectors(reports)
    ids = [r.get('id') for r in reports]

    # save vocab and ids as json
    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False)
    with open(IDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ids, f, ensure_ascii=False)

    # save matrix as npz
    try:
        np.savez_compressed(MATRIX_FILE, matrix=matrix)
    except Exception:
        # fallback: save as raw binary
        np.save(MATRIX_FILE + '.npy', matrix)

    # write last-built metadata
    meta = {'count': len(ids), 'last_built': datetime.now(timezone.utc).isoformat()}
    try:
        with open(os.path.join(EMB_DIR, 'last_built.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f)
    except Exception:
        pass

    return {'status': 'success', 'count': len(ids), 'last_built': meta['last_built']}


def load_index() -> Tuple[Dict, np.ndarray, List[str]]:
    """Return (vocab, matrix, ids) if available, else (None, None, None)."""
    if not os.path.exists(VOCAB_FILE) or not os.path.exists(IDS_FILE):
        return None, None, None
    try:
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        with open(IDS_FILE, 'r', encoding='utf-8') as f:
            ids = json.load(f)
        # load matrix
        if os.path.exists(MATRIX_FILE):
            data = np.load(MATRIX_FILE, allow_pickle=True)
            matrix = data['matrix']
        elif os.path.exists(MATRIX_FILE + '.npy'):
            matrix = np.load(MATRIX_FILE + '.npy', allow_pickle=True)
        else:
            return None, None, None
        return vocab, matrix, ids
    except Exception:
        return None, None, None


def search_index(query: str, top_n: int = 5) -> List[Dict]:
    """Search persisted index and return top_n results with scores."""
    vocab, matrix, ids = load_index()
    if vocab is None or matrix is None or ids is None:
        return []

    qv = _vectorize(query, vocab)
    if matrix.size == 0:
        return []
    scores = (matrix @ qv)
    idxs = np.argsort(-scores)[:top_n]
    results = []
    for i in idxs:
        score = float(scores[i])
        results.append({'id': ids[i], 'score': round(score, 4)})
    return results


def get_index_status() -> Dict:
    """Return stored index metadata if available."""
    meta_file = os.path.join(EMB_DIR, 'last_built.json')
    if not os.path.exists(meta_file):
        return {'count': 0, 'last_built': None}
    try:
        with open(meta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'count': 0, 'last_built': None}
