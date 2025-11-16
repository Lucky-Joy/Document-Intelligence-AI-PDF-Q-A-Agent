import os
from typing import Iterable
from functools import lru_cache

import streamlit as st
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

@lru_cache(maxsize=1)
def load_sbert():
    return SentenceTransformer("all-MiniLM-L6-v2")

class EmbeddingStore:
    def __init__(self, path: str = "./.data/vector_store", prefer_persistent: bool = True):
        os.makedirs(path, exist_ok=True)
        self.model = load_sbert()
        self._persistent = False
        self._path = path
        self._init_error = None

        if prefer_persistent:
            try:
                settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=path)
                self.client = chromadb.Client(settings)
                self.col = self._get_collection("cerevyn_docs")
                self._persistent = True
                st.info("Chroma: persistent store initialized.")
                return
            except Exception as e:
                self._init_error = e
                st.warning(f"Chroma persistent init failed. Falling back to in-memory store. ({type(e).__name__}: {str(e)})")

        try:
            self.client = chromadb.Client()
            self.col = self._get_collection("cerevyn_docs")
            self._persistent = False
            st.info("Chroma: using in-memory store.")
        except Exception as e:
            st.error(f"Fatal: unable to initialize Chroma in any mode: {e}")
            raise

    def _get_collection(self, name: str):
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(name)

    def add_documents(self, doc_id: str, chunks: Iterable[dict], batch_size: int = 32):
        ids_batch, texts_batch, mets_batch = [], [], []
        for c in chunks:
            cid = f"{doc_id}-{c.get('chunk_id','')}"
            ids_batch.append(cid)
            texts_batch.append(c["text"])
            mets_batch.append({"doc_id": doc_id, "page": str(c.get("page", ""))})
            if len(texts_batch) >= batch_size:
                embs = self.model.encode(texts_batch, convert_to_numpy=True)
                embs_list = embs.tolist() if isinstance(embs, (list, np.ndarray)) else [list(e) for e in embs]
                try:
                    self.col.add(documents=texts_batch, metadatas=mets_batch, ids=ids_batch, embeddings=embs_list)
                except Exception as e:
                    st.warning(f"Chroma add batch failed: {e}")
                ids_batch, texts_batch, mets_batch = [], [], []
        if texts_batch:
            embs = self.model.encode(texts_batch, convert_to_numpy=True)
            embs_list = embs.tolist() if isinstance(embs, (list, np.ndarray)) else [list(e) for e in embs]
            try:
                self.col.add(documents=texts_batch, metadatas=mets_batch, ids=ids_batch, embeddings=embs_list)
            except Exception as e:
                st.warning(f"Chroma add final batch failed: {e}")
        if getattr(self, "_persistent", False):
            try:
                self.client.persist()
            except Exception:
                pass

    def query(self, q: str, k: int = 3):
        vec = self.model.encode([q], convert_to_numpy=True).tolist()[0]
        try:
            res = self.col.query(vector=vec, n_results=k, include=["metadatas", "distances", "documents", "ids"])
        except Exception as e:
            st.warning(f"Chroma query failed: {e}")
            return []
        items = []
        docs = res.get("documents", [[]])[0] if res.get("documents") else []
        metas = res.get("metadatas", [[]])[0] if res.get("metadatas") else []
        dists = res.get("distances", [[]])[0] if res.get("distances") else []
        ids = res.get("ids", [[]])[0] if res.get("ids") else []
        for doc, meta, dist, idd in zip(docs, metas, dists, ids):
            try:
                page_num = int(meta.get("page", 0))
            except Exception:
                page_num = 0
            items.append({"text": doc, "doc_id": meta.get("doc_id"), "page": page_num, "score": 1.0 - dist})
        return items
