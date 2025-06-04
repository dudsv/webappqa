import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def clean_text(text):
    """
    Limpa o texto removendo links e espaços extras.
    """
    if not isinstance(text, str):
        return ""
    # Remove links (http, www, etc.) e parênteses vazios
    text = re.sub(
        r'\s*(?:([^()]?(?:https?://|www.|/)[^()]?)|(?:https?://|www.|/)[^\s()]+)\s*',
        ' ',
        text
    )
    text = re.sub(r'(\s*)', '', text)
    # Colapsa espaços extras, mas preserva espaço antes da pontuação
    text = re.sub(r'\s+|(\s+)(?=[.,!?:;])', lambda m: '' if m.group(1) else ' ', text)
    return text.strip()

def safe_best_match(query, candidates):
    """
    Retorna (best_text, similarity) ou ("", 0.0).
    Evita erro "empty vocabulary" quando nenhum texto útil é encontrado.
    """
    query = clean_text(query.lower())
    candidates_clean = [clean_text(c.lower()) for c in candidates if clean_text(c)]
    if not query or not candidates_clean:
        return "", 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        corpus = [query] + candidates_clean
        tfidf = vectorizer.fit_transform(corpus)
        sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
        idx_max = sims.argmax()
        return candidates[idx_max], float(sims[idx_max])
    except ValueError:
        return "", 0.0

def compare_texts(docx_list, html_list, metadata, alt_tags):
    """
    Compara textos do documento DOCX com conteúdo HTML e metadados.
    """
    results = []

    for doc_text in docx_list:
        if not doc_text.strip():
            continue
        clean_doc = clean_text(doc_text.strip().lower())
        ignore_prefixes = [
            "in dit artikel", "title tag:", "meta description:", "og title:", "og description:",
            "[alt text da imagem]", "alt tag :", "title tag", "meta description",
            "open graph title", "open graph description", "-- meta --", "en:", "be-fr:",
            "guide des races de chiens", "alt-tag:", "-- meta –", "title tag"
        ]
        if any(clean_doc.startswith(p) for p in ignore_prefixes):
            continue
        # "alt-tag" block
        if clean_doc.startswith("alt-tag"):
            original_alt = doc_text.split(":", 1)[1].strip()
            match_text, score = safe_best_match(original_alt, alt_tags)
            if score >= 0.85:
                status = "Exact"
            elif score >= 0.75:
                status = "Similar"
            elif score >= 0.4:
                status = "Partial"
            else:
                status = "Missing"
            results.append({
                "Document Text": original_alt,
                "Webpage Match": match_text,
                "Status": status,
                "Similarity": round(score * 100, 1)
            })
            continue
        # Check exact match in metadata
        meta_type = next((k for k, v in metadata.items() if v and doc_text.strip() == v.strip()), None)
        if not meta_type:
            best_meta = ""
            best_score = 0.0
            for k, v in metadata.items():
                if not v.strip():
                    continue
                _, sim = safe_best_match(doc_text, [v])
                if sim > best_score:
                    best_score = sim
                    best_meta = k
            if best_score > 0.85:
                meta_type = best_meta
        if meta_type:
            sim_meta = safe_best_match(doc_text, [metadata[meta_type]])[1]
            if sim_meta >= 0.85:
                status = "Exact"
            elif sim_meta >= 0.75:
                status = "Similar"
            elif sim_meta >= 0.4:
                status = "Partial"
            else:
                status = "Missing"
            results.append({
                "Document Text": doc_text,
                "Webpage Match": metadata[meta_type],
                "Status": status,
                "Similarity": round(sim_meta * 100, 1)
            })
            continue
        # Otherwise compare against HTML blocks
        match_html, score_html = "", 0.0
        if html_list:
            match_html, score_html = safe_best_match(doc_text, html_list)
        if score_html >= 0.85:
            status = "Exact"
        elif score_html >= 0.75:
            status = "Similar"
        elif score_html >= 0.4:
            status = "Partial"
        else:
            status = "Missing"
        results.append({
            "Document Text": doc_text,
            "Webpage Match": match_html,
            "Status": status,
            "Similarity": round(score_html * 100, 1)
        })
    return pd.DataFrame(results)

def generate_summary(df):
    """
    Gera um resumo estatístico dos resultados da comparação.
    """
    total = len(df)
    summary_counts = df["Status"].value_counts().reindex(
        ["Exact", "Similar", "Partial", "Missing"], fill_value=0
    )
    percentages = (summary_counts / total * 100).round(1) if total > 0 else [0, 0, 0, 0]
    df_summary = pd.DataFrame({
        "Status": summary_counts.index,
        "Quantidade": summary_counts.values,
        "Porcentagem": percentages.values
    })
    df_summary.loc[len(df_summary.index)] = ["TOTAL", total, f"{100 if total > 0 else 0}%"]
    return df_summary
