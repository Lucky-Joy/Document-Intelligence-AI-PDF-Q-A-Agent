import streamlit as st

def _extractive_answer(snippets):
    out = []
    for s in snippets[:4]:
        txt = s.get("text", "").replace("\n", " ").strip()
        out.append(f"{txt} [source: {s.get('doc_id')} p.{s.get('page')}]")
    return " ".join(out)

def synthesize_answer(question: str, snippets: list, mode: str = "extractive"):
    base_context = "\n\n".join([f"[{s['doc_id']} p.{s['page']}] {s['text']}" for s in snippets])
    if mode == "openai":
        key = None
        try:
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            key = None
        if not key:
            return _extractive_answer(snippets)
        try:
            import openai
            openai.api_key = key
            prompt = f"Question: {question}\n\nContext:\n{base_context}\n\nWrite a concise answer (max 120 words) and include citations like [p.4]. If uncertain, say 'I am not sure' and cite sources."
            resp = openai.Completion.create(model="text-davinci-003", prompt=prompt, max_tokens=200, temperature=0.0)
            text = resp.choices[0].text.strip()
            return text
        except Exception:
            return _extractive_answer(snippets)
    return _extractive_answer(snippets)