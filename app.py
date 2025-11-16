import os
from pathlib import Path
from typing import List

import streamlit as st

from utils.pdf_parser import parse_pdf_bytes, save_pdf_bytes
from utils.chunker import iter_chunks
from utils.embeddings_store import EmbeddingStore
from utils.retriever import retrieve
from utils.highlight_renderer import render_page_with_highlights
from utils.table_extractor import detect_tables_and_extract
from services.llm_client import synthesize_answer

st.set_page_config(page_title="Cerevyn Document Intelligence", layout="wide")
st.title("Cerevyn — Document Intelligence")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", 50))
MAX_PAGES = int(os.getenv("MAX_PAGES", 200))
DEFAULT_ANSWER_LEN = 3
DEFAULT_BATCH = int(os.getenv("EMB_BATCH", 32))
UPLOAD_DIR = Path(".data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@st.cache_resource(ttl=60 * 60 * 24)
def get_store():
    return EmbeddingStore(path="./.data/vector_store")

st.session_state.setdefault("store", get_store())
st.session_state.setdefault("docs_meta", {})

col_main, col_side = st.columns([2, 1])

with col_main:
    st.header("Upload & index your PDFs")
    st.write("Upload one or more PDFs you own (example: project report, manual). After selecting files, click **Index uploaded PDFs**.")
    uploaded_files = st.file_uploader(
        "Select PDF(s) to upload",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.markdown("**Files ready for indexing:**")
        for f in uploaded_files:
            st.write(f"- {f.name} — {f.size / (1024*1024):.2f} MB")
            if f.size > MAX_UPLOAD_MB * 1024 * 1024:
                st.warning(f"{f.name} exceeds the {MAX_UPLOAD_MB} MB suggestion and may be skipped.")

        if st.button("Index uploaded PDFs"):
            with st.spinner("Parsing and indexing — this may take a short while..."):
                for f in uploaded_files:
                    fname = f.name
                    size_mb = f.size / (1024*1024)
                    if size_mb > MAX_UPLOAD_MB:
                        st.error(f"Skipping {fname}: file too large ({size_mb:.1f} MB).")
                        continue

                    pdf_bytes = f.read()
                    saved_path = save_pdf_bytes(fname, pdf_bytes, base_dir=UPLOAD_DIR)

                    try:
                        pages = parse_pdf_bytes(pdf_bytes)
                    except Exception as e:
                        st.error(f"Failed to parse {fname}: {e}")
                        continue

                    if not pages:
                        st.warning(f"No text extracted from {fname}; it may be a scanned PDF. Consider OCR if needed.")
                        continue

                    if len(pages) > MAX_PAGES:
                        st.warning(f"{fname} has {len(pages)} pages; indexing first {MAX_PAGES} pages.")
                        pages = pages[:MAX_PAGES]

                    chunk_gen = iter_chunks(pages, chunk_chars=1200, overlap=200)
                    try:
                        st.session_state["store"].add_documents(doc_id=fname, chunks=chunk_gen, batch_size=DEFAULT_BATCH)
                    except Exception as e:
                        st.error(f"Indexing error for {fname}: {e}")
                        continue

                    st.session_state["docs_meta"][fname] = {
                        "name": fname,
                        "path": str(saved_path),
                        "pages": len(pages)
                    }
                    st.success(f"Indexed {fname} (pages: {len(pages)})")

    st.markdown("---")
    st.header("Ask a question")
    st.write("Type a natural-language question about the PDFs you indexed. The answer will include short excerpts and page references.")
    q = st.text_input("Your question")
    answer_len = st.slider(
        "Answer length — how concise or detailed should the answer be?",
        min_value=1, max_value=6, value=DEFAULT_ANSWER_LEN,
        help="1 = concise (short), 6 = detailed (longer, more context)"
    )
    top_k = int(answer_len)

    if st.button("Get answer") and q.strip():
        if not st.session_state["docs_meta"]:
            st.warning("No documents indexed yet. Upload and index PDFs first.")
        else:
            with st.spinner("Searching for the best answer..."):
                results, confidence = retrieve(st.session_state["store"], q, k=top_k)

            st.write("Debug: raw retrieval results:", results, "Confidence:", confidence)

            if not results:
                st.info("No relevant passages found. Try rephrasing the question or index more documents.")
            else:
                snippets = []
                for r in results:
                    snippets.append({
                        "text": r["text"],
                        "page": r["page"],
                        "doc_id": r["doc_id"],
                        "score": r["score"]
                    })

                answer = synthesize_answer(q, snippets, mode="extractive")

                st.subheader("Answer")
                st.info(answer)
                try:
                    st.progress(int(max(0.0, min(1.0, confidence)) * 100))
                except Exception:
                    pass
                st.write(f"Confidence: {confidence:.2f}")

                st.subheader("Sources & snippets")
                for s in snippets:
                    st.write(f"**{s['doc_id']} — p.{s['page']} — score {s['score']:.3f}**")
                    st.code(s["text"][:800])
                    key = f"show-{s['doc_id']}-{s['page']}-{abs(hash(s['text']))}"
                    if st.button(f"Show highlighted page {s['doc_id']} p.{s['page']}", key=key):
                        docmeta = st.session_state["docs_meta"].get(s["doc_id"])
                        if docmeta and docmeta.get("path"):
                            img_bytes = render_page_with_highlights(docmeta["path"], int(s["page"]), highlights=[s])
                            st.image(img_bytes, use_column_width=True)
                        else:
                            st.warning("Original PDF not found for rendering highlights.")

    with st.expander("Advanced (debug)"):
        if st.button("Show indexed docs (debug)"):
            st.write("Indexed docs:", list(st.session_state["docs_meta"].keys()))
            try:
                col = st.session_state["store"].col
                st.write("Vector store collection:", getattr(col, "name", "unknown"))
            except Exception as e:
                st.write("Vector store info not available:", e)

with col_side:
    st.header("Document viewer")
    choices = ["(none)"] + list(st.session_state["docs_meta"].keys())
    sel = st.selectbox("Select a document to preview", choices)
    if sel != "(none)":
        meta = st.session_state["docs_meta"][sel]
        page_num = st.number_input("Page number", min_value=1, max_value=meta["pages"], value=1)
        img_bytes = render_page_with_highlights(meta["path"], int(page_num), highlights=[])
        st.image(img_bytes, use_column_width=True)

        st.markdown("### Table detection (page preview)")
        try:
            import fitz
            doc = fitz.open(meta["path"])
            p = doc.load_page(page_num - 1)
            text = p.get_text()
            doc.close()
        except Exception:
            text = ""
        tables = detect_tables_and_extract(text)
        if tables:
            st.write(f"Detected {len(tables)} table(s); preview (best-effort):")
            for i, t in enumerate(tables):
                st.write(f"Table {i+1} (rows {len(t['rows'])})")
                st.dataframe(t["preview"])
        else:
            st.write("No tables detected on this page (or extraction deferred).")