from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class PageObj:
    number: int
    text: str

def parse_with_fitz(pdf_bytes: bytes) -> List[PageObj]:
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i in range(doc.page_count):
        p = doc.load_page(i)
        text = p.get_text("text") or ""
        pages.append(PageObj(number=i + 1, text=text))
    doc.close()
    return pages

def parse_with_pdfminer(pdf_bytes: bytes) -> List[PageObj]:
    from io import BytesIO
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams

    pages = []
    fp = BytesIO(pdf_bytes)
    output = BytesIO()
    laparams = LAParams()
    extract_text_to_fp(fp, output, laparams=laparams, output_type='text', codec='utf-8')
    text = output.getvalue().decode('utf-8', errors='ignore')
    raw_pages = text.split("\f") if "\f" in text else text.split("\n\n\n")
    for idx, ptext in enumerate(raw_pages):
        ptext = ptext.strip()
        if ptext:
            pages.append(PageObj(number=idx + 1, text=ptext))
    return pages

def parse_pdf_bytes(pdf_bytes: bytes) -> List[PageObj]:
    try:
        return parse_with_fitz(pdf_bytes)
    except Exception:
        try:
            return parse_with_pdfminer(pdf_bytes)
        except Exception as e:
            return []

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
