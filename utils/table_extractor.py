import re
import pandas as pd
from typing import List, Dict

def detect_tables_and_extract_text(page_text: str):
    lines = [ln.rstrip() for ln in page_text.splitlines() if ln.strip()]
    if not lines:
        return []

    table_lines = [ln for ln in lines if len(re.findall(r"\s{2,}", ln)) >= 1]
    if len(table_lines) < 2:
        return []

    rows = []
    for ln in table_lines:
        cols = [c.strip() for c in re.split(r"\s{2,}", ln) if c.strip()]
        rows.append(cols)

    maxc = max(len(r) for r in rows)
    data = [r + [""] * (maxc - len(r)) for r in rows]
    df = pd.DataFrame(data)
    preview = df.head(50)
    return [{"rows": rows, "preview": preview}]