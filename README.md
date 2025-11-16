---

# 📘 Cerevyn – Document Intelligence (PDF Q&A System)

An intelligent PDF Question-Answering system.
Upload one or more PDFs → the system indexes them → ask any question → get answers with page references, source snippets, and highlighted evidence.

---

## 🚀 Features

### 🔍 **Smart PDF Understanding**

* Upload multiple PDFs (reports, manuals, etc.)
* Clean text extraction using PyMuPDF
* Streaming chunking (memory-efficient even for large PDFs)

### 🧠 **AI-Powered Retrieval**

* Embedding-based search using **Sentence Transformers**
* Vector database powered by **Chroma**
* Confidence scores for every answer

### 📝 **Natural Answers with Citations**

* Extractive answer generation
* Each answer includes:

  * Relevant text excerpts
  * Page numbers
  * Document names

### 🖼️ **Evidence Highlighting**

* View the exact PDF page with highlighted relevant text
* Works even with multiple sources

### 📊 **Table Detection (Best-Effort)**

* Detects table-like text patterns
* Shows a preview in DataFrame format

---

## 🧩 Tech Stack

* **Streamlit** – Web UI
* **PyMuPDF** – PDF parsing & rendering
* **Sentence-Transformers** – Embeddings
* **ChromaDB** – Vector store
* **Pillow** – Rendering highlights
* **Pandas** – Table preview

---

## 💻 How to Run Locally

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

**Windows PowerShell**

```bash
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python -m streamlit run app.py
```

Then open the link shown in the terminal (usually [http://localhost:8501](http://localhost:8501)).

---

## 📁 Project Structure

```
app.py
requirements.txt
utils/
    pdf_parser.py
    chunker.py
    embeddings_store.py
    retriever.py
    highlight_renderer.py
    table_extractor.py
services/
    llm_client.py
```

---

## 🌐 Deployment

This application is deployable directly from GitHub using:

* **Streamlit Community Cloud** (recommended)
* **Render** (fallback option)

The deployed link is included in the submission.

---

## 📝 Notes

* No external API keys required (extractive answer mode).
* OCR is not included (only digital PDFs recommended).
* Vector store and runtime data are not committed to the repository.

---

## 🙌 Author

Built by **Lucky Joy Tutika**

---
