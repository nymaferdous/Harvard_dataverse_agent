"""
rag_metadata_generator.py
--------------------------
FREE, local, zero-API-cost metadata generation using RAG.

Pipeline:
  1. Extract features from the uploaded file (column names, sample values,
     filename hints, detected time range, detected geographic coverage).
  2. Encode those features as a short text query using sentence-transformers
     (runs 100 % locally — no internet, no API key, no cost).
  3. Cosine-similarity search over the knowledge base of ~20 domain examples.
  4. Retrieve the top-3 closest entries and blend their keywords / subject.
  5. Fill a metadata template, substituting detected file-specific values
     (title, time range, data source, geographic coverage) over the template.

Supported file types: CSV, TXT, MD
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from modules.rag_metadata_kb import KNOWLEDGE_BASE

# ---------------------------------------------------------------------------
# Lazy-load the sentence-transformer model (downloaded once, cached locally)
# ---------------------------------------------------------------------------

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # noqa: import here to keep startup fast
        print("[RAGMetadata] Loading sentence-transformers model (first run may take ~30 s)…")
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print("[RAGMetadata] Model ready.")
    return _MODEL


# ---------------------------------------------------------------------------
# Pre-compute KB embeddings (cached after first call)
# ---------------------------------------------------------------------------

_KB_EMBEDDINGS: Optional[np.ndarray] = None


def _get_kb_embeddings() -> np.ndarray:
    global _KB_EMBEDDINGS
    if _KB_EMBEDDINGS is None:
        model = _get_model()
        texts = [entry["text"] for entry in KNOWLEDGE_BASE]
        _KB_EMBEDDINGS = model.encode(texts, normalize_embeddings=True)
    return _KB_EMBEDDINGS


# ---------------------------------------------------------------------------
# File feature extraction
# ---------------------------------------------------------------------------

_MONTH_NAMES = {
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april", "june",
    "july", "august", "september", "october", "november", "december",
}

_GEO_HINTS = {
    "country", "region", "continent", "area", "territory",
    "nation", "state", "province", "zone", "location",
    "latitude", "longitude", "lat", "lon", "lng", "coord",
}

_TIME_HINTS = {
    "year", "date", "month", "time", "period", "quarter",
    "yr", "dt", "timestamp", "datetime",
}


def _detect_years(values: List[str]) -> Tuple[str, str]:
    """Try to extract min/max 4-digit years from a list of values."""
    years = []
    for v in values:
        matches = re.findall(r"\b(1[89]\d{2}|20[0-2]\d)\b", str(v))
        years.extend(int(m) for m in matches)
    if years:
        return str(min(years)), str(max(years))
    return "", ""


def extract_file_features(
    file_path: str,
    max_rows: int = 30,
    original_filename: str = "",
) -> Dict[str, Any]:
    """
    Extract semantic and structural features from a dataset file.

    Returns a dict with:
      - query_text:          string fed into the sentence-transformer
      - title_hint:          candidate title derived from filename + columns
      - columns:             list of column names (CSV only)
      - time_period_start:   detected or ""
      - time_period_end:     detected or ""
      - geographic_coverage: detected or ""
      - data_source:         guessed from filename
      - sample_text:         raw text preview
    """
    path = Path(file_path)
    # Use original_filename if supplied so temp-file names don't leak into titles
    display_name = original_filename if original_filename else path.name
    stem = Path(display_name).stem.replace("_", " ").replace("-", " ")

    features: Dict[str, Any] = {
        "query_text": stem,
        "title_hint": stem.title() if stem.islower() or stem.isupper() else stem,
        "columns": [],
        "time_period_start": "",
        "time_period_end": "",
        "geographic_coverage": "",
        "data_source": stem.title(),
        "sample_text": "",
    }

    if path.suffix.lower() == ".csv":
        try:
            rows: List[List[str]] = []
            with open(path, newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i > max_rows:
                        break
                    rows.append(row)

            if not rows:
                return features

            headers = [h.strip() for h in rows[0]]
            features["columns"] = headers

            # Build a rich query text from column names + sample values
            header_text = " ".join(headers).lower()
            sample_values: List[str] = []
            for row in rows[1:6]:
                sample_values.extend(str(v).strip() for v in row if v.strip())

            features["query_text"] = f"{stem} {header_text} {' '.join(sample_values[:40])}"
            features["sample_text"] = "\n".join(",".join(r) for r in rows[:6])

            # Guess title from filename + column count
            # Title is just the clean filename stem — no variable count suffix
            features["title_hint"] = stem.title() if stem.islower() or stem.isupper() else stem

            # Detect time columns → year range
            time_cols = [h for h in headers if any(t in h.lower() for t in _TIME_HINTS)]
            if time_cols:
                col_idx = headers.index(time_cols[0])
                col_vals = [row[col_idx] for row in rows[1:] if len(row) > col_idx]
                start, end = _detect_years(col_vals)
                features["time_period_start"] = start
                features["time_period_end"] = end

            # Detect geographic column → coverage hint
            geo_cols = [h for h in headers if any(g in h.lower() for g in _GEO_HINTS)]
            if geo_cols:
                col_idx = headers.index(geo_cols[0])
                geo_vals = list({
                    row[col_idx].strip()
                    for row in rows[1:]
                    if len(row) > col_idx and row[col_idx].strip()
                })
                if len(geo_vals) == 1:
                    features["geographic_coverage"] = geo_vals[0]
                elif 1 < len(geo_vals) <= 5:
                    features["geographic_coverage"] = ", ".join(geo_vals[:5])
                else:
                    features["geographic_coverage"] = "Global"

            # Guess data source from filename
            upper = path.stem.upper()
            if "FAOSTAT" in upper or "FAO" in upper:
                features["data_source"] = "FAO FAOSTAT"
            elif "IRENA" in upper:
                features["data_source"] = "IRENA"
            elif "IEA" in upper:
                features["data_source"] = "IEA"
            elif "COMTRADE" in upper or "TRADE" in upper:
                features["data_source"] = "UN Comtrade"
            elif "GBIF" in upper:
                features["data_source"] = "GBIF"
            elif "WHO" in upper:
                features["data_source"] = "WHO"
            elif "EEA" in upper:
                features["data_source"] = "European Environment Agency"

        except Exception as exc:
            print(f"[RAGMetadata] CSV parse warning: {exc}")

    elif path.suffix.lower() in (".txt", ".md"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")[:3000]
            features["query_text"] = f"{stem} {content[:500]}"
            features["sample_text"] = content[:500]
        except Exception as exc:
            print(f"[RAGMetadata] Text read warning: {exc}")

    return features


# ---------------------------------------------------------------------------
# Similarity retrieval
# ---------------------------------------------------------------------------

def retrieve_top_k(query_text: str, k: int = 3) -> List[Dict[str, Any]]:
    """Return the top-k knowledge base entries most similar to query_text."""
    model = _get_model()
    kb_embeddings = _get_kb_embeddings()

    query_embedding = model.encode([query_text], normalize_embeddings=True)[0]
    scores = kb_embeddings @ query_embedding  # cosine similarity (already normalised)

    top_indices = np.argsort(scores)[::-1][:k]
    results = []
    for idx in top_indices:
        entry = KNOWLEDGE_BASE[idx]
        results.append({"score": float(scores[idx]), **entry})
        print(f"[RAGMetadata] Match #{len(results)}: score={scores[idx]:.3f}  "
              f"→ {entry['metadata']['title'][:60]}")
    return results


# ---------------------------------------------------------------------------
# Template filling
# ---------------------------------------------------------------------------

def _blend_keywords(matches: List[Dict[str, Any]], max_kw: int = 6) -> List[str]:
    """Merge keywords from top matches, de-duplicated, preserving order."""
    seen: set = set()
    result: List[str] = []
    for m in matches:
        for kw in m["metadata"].get("keywords", []):
            key = kw.lower()
            if key not in seen:
                seen.add(key)
                result.append(kw)
            if len(result) >= max_kw:
                return result
    return result


def fill_metadata_template(
    matches: List[Dict[str, Any]],
    features: Dict[str, Any],
    author_name: str = "",
    author_affiliation: str = "",
    contact_email: str = "",
) -> Dict[str, Any]:
    """Combine the best KB match with file-specific detected features."""
    best = matches[0]["metadata"]

    # Title: use filename hint if informative, else fall back to KB template
    title_hint = features.get("title_hint", "").strip()
    title = title_hint if len(title_hint) > 5 else best["title"]

    # Description: use KB template description (it's domain-appropriate)
    description = best["description"]

    # Keywords: blend top-3 matches
    keywords = _blend_keywords(matches)

    # Subject: from best match
    subject = best["subject"]

    # Geographic coverage: prefer detected, fall back to KB
    geo = features.get("geographic_coverage") or best.get("geographic_coverage", "Global")

    # Time period: prefer detected, fall back to KB
    t_start = features.get("time_period_start") or best.get("time_period_start", "")
    t_end   = features.get("time_period_end")   or best.get("time_period_end", "")

    # Data source: prefer filename-detected, fall back to KB
    data_source = features.get("data_source") or best.get("data_source", "")

    return {
        "title": title,
        "description": description,
        "keywords": keywords,
        "subject": subject,
        "geographic_coverage": geo,
        "time_period_start": t_start,
        "time_period_end": t_end,
        "data_source": data_source,
        "license": "CC0 1.0",
        "related_publication": "",
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_metadata_rag(
    file_path: str,
    author_name: str = "",
    author_affiliation: str = "",
    contact_email: str = "",
    original_filename: str = "",
) -> Dict[str, Any]:
    """
    Full RAG metadata pipeline — completely free, runs locally.

    Args:
        file_path:           Path to the dataset file (CSV, TXT, MD).
        author_name:         Author name (passed through to schema builder).
        author_affiliation:  Author institution.
        contact_email:       Contact email.
        original_filename:   The user's real filename (avoids temp-file names in titles).

    Returns:
        Dict with metadata fields ready for build_dataverse_metadata().
    """
    display = original_filename or Path(file_path).name
    print(f"[RAGMetadata] Extracting features from '{display}'…")
    features = extract_file_features(file_path, original_filename=original_filename)

    print(f"[RAGMetadata] Querying knowledge base…")
    matches = retrieve_top_k(features["query_text"], k=3)

    metadata = fill_metadata_template(matches, features, author_name, author_affiliation, contact_email)

    print(f"[RAGMetadata] Generated metadata:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")

    return metadata
