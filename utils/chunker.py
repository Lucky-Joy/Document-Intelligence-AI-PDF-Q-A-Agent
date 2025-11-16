import re
from typing import Generator

def page_chunk_generator(page, chunk_chars=1200, overlap=200):
    txt = (page.text or "").strip()
    if not txt:
        return
    start = 0
    L = len(txt)
    while start < L:
        end = min(L, start + chunk_chars)
        if end < L:
            window = txt[start:end]
            br = window.rfind("\n")
            bs = window.rfind(". ")
            if br != -1 and end - (start + br) <= 200:
                end = start + br + 1
            elif bs != -1 and end - (start + bs) <= 200:
                end = start + bs + 2
        chunk_text = txt[start:end].strip()
        if chunk_text:
            yield {
                "text": chunk_text,
                "page": page.number,
                "start_char": start,
                "end_char": end
            }
        next_start = end - overlap
        start = next_start if next_start > start else end

def iter_chunks(pages, chunk_chars=1200, overlap=200):
    idx = 0
    for p in pages:
        for c in page_chunk_generator(p, chunk_chars=chunk_chars, overlap=overlap):
            c["chunk_id"] = f"c{idx}"
            idx += 1
            yield c