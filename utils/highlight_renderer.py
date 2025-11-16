from io import BytesIO
from typing import List
import fitz
from PIL import Image

def render_page_with_highlights(pdf_path: str, page_number: int, highlights: List[dict]):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number - 1)
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    from PIL import ImageDraw
    draw = ImageDraw.Draw(img, "RGBA")

    for h in highlights:
        bbox = h.get("bbox")
        if not bbox and "text" in h and h["text"]:
            try:
                text = h["text"].strip()[:200]
                areas = page.search_for(text)
                if areas:
                    bbox = areas[0]
            except Exception:
                bbox = None
        if bbox:
            x0, y0, x1, y1 = bbox
            x0_i = int(x0 * zoom)
            y0_i = int(y0 * zoom)
            x1_i = int(x1 * zoom)
            y1_i = int(y1 * zoom)
            draw.rectangle([x0_i, y0_i, x1_i, y1_i], outline=(255,165,0,220), fill=(255,165,0,60), width=3)

    bio = BytesIO()
    img.save(bio, format="PNG")
    doc.close()
    bio.seek(0)
    return bio.getvalue()