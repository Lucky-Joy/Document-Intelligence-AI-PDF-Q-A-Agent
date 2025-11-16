import fitz
from dataclasses import dataclass
from pathlib import Path
from typing import List
import os

@dataclass
class PageObj:
    number: int
    text: str

def parse_pdf_bytes(pdf_bytes: bytes) -> List[PageObj]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i in range(doc.page_count):
        p = doc.load_page(i)
        text = p.get_text("text") or ""
        pages.append(PageObj(number=i + 1, text=text))
    doc.close()
    return pages

def save_pdf_bytes(orig_name: str, pdf_bytes: bytes, base_dir: Path):
    base_dir.mkdir(parents=True, exist_ok=True)
    safe_name = orig_name.replace(" ", "_")
    out = base_dir / safe_name
    if out.exists():
        stem = out.stem
        suffix = out.suffix
        i = 1
        while (base_dir / f"{stem}_{i}{suffix}").exists():
            i += 1
        out = base_dir / f"{stem}_{i}{suffix}"
    with open(out, "wb") as fh:
        fh.write(pdf_bytes)
    return out