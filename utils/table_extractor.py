import pandas as pd
import re


def detect_tables_and_extract(page_text: str):
    if not page_text or len(page_text.strip()) == 0:
        return []

    lines = [l.strip() for l in page_text.split("\n")]
    lines = [l for l in lines if l]

    tables = []
    current = []

    def flush():
        if not current:
            return
        rows = []
        for row in current:
            cols = re.split(r"\s{2,}", row.strip())
            rows.append(cols)
        try:
            df = pd.DataFrame(rows)
        except Exception:
            df = None
        tables.append({"rows": rows, "preview": df})

    for line in lines:
        if re.search(r"\S+\s{2,}\S+", line):
            current.append(line)
        else:
            flush()
            current = []

    flush()
    return tables
