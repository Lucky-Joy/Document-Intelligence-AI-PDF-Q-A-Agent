from typing import Tuple, List

def retrieve(store, query: str, k: int = 3) -> Tuple[List[dict], float]:
    hits = store.query(query, k)
    if not hits:
        return [], 0.0
    scores = [h.get("score", 0.0) for h in hits]
    top = max(scores)
    conf = float(top)
    return hits, conf