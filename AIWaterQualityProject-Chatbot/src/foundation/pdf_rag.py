"""RAG over the Methodology PDF (standards / rules part only).

What is indexed
---------------
Only the standards / rules content of ``Data/Standards/Methodology___Results____Discussion.pdf``:

* the text of section **3.2.2** (WHO weighted-arithmetic WQI, Eq. 1-3, WQI bands,
  microbial rule, risk-score rule, worst-penalty-wins rule) -- i.e. every paragraph
  *above* Table 1, starting from the 3.2.2 heading, and
* **Table 1** (penalty mapping), indexed both as one whole-table chunk and as one
  chunk per table row.

Everything else in the PDF (EDA findings, model results, figures, ...) is ignored.
To index more sections later, add their numbers to ``INCLUDE_SECTIONS``.

Storage
-------
Chunks are embedded with the project's existing Gemini embedding model
(``vector_store._embedder``, default ``models/gemini-embedding-001``) and saved in the
same ``chroma_db`` folder, in their own collection (``methodology_rules``). The existing
``water_standards`` collection is never touched by this module.

Usage
-----
    python src/main.py --ingest-pdf          # build / rebuild the collection
    python -m src.foundation.pdf_rag --preview   # show the chunks, no API key needed
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.foundation.vector_store import (
    DB_DIR,
    STANDARDS_DIR,
    _embedder,
    _get_query_embedding,
)

METHODOLOGY_COLLECTION = "methodology_rules"
PDF_GLOB = "Methodology*.pdf"

# Section numbers whose text is indexed (heading line to the next numbered heading).
INCLUDE_SECTIONS = ["3.2.2"]

MAX_CHARS = 900          # target upper size of a text chunk
OVERLAP_MAX_CHARS = 300  # a trailing unit up to this size is repeated in the next chunk

_HEADING_RE = re.compile(r"^(\d\.\d(?:\.\d)?)\s+([A-Z].*)$")
_EQUATION_RE = re.compile(r"=.*\(\d\)\s*$")
_TABLE_CAPTION_RE = re.compile(r"^Table\s+1\.", re.I)


# --------------------------------------------------------------------------- #
# PDF reading
# --------------------------------------------------------------------------- #
def find_pdf() -> Path:
    matches = sorted(STANDARDS_DIR.glob(PDF_GLOB))
    if not matches:
        raise FileNotFoundError(
            f"Methodology PDF not found in {STANDARDS_DIR} (expected a file matching '{PDF_GLOB}')."
        )
    return matches[0]


def _read_pdf(pdf_path: Path) -> Tuple[str, List[List[List[str]]]]:
    """Returns (full_text, tables). `tables` is empty if only a text-only reader is available."""
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
            tables = []
            for page in pdf.pages:
                tables.extend(page.extract_tables() or [])
        return text, tables
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return "\n".join((p.extract_text() or "") for p in reader.pages), []
    except ImportError:
        raise ImportError("Reading the methodology PDF needs a PDF library. Run: pip install pdfplumber")


def _split_sections(full_text: str) -> Dict[str, Dict[str, str]]:
    """Split the text into {section_number: {"title": ..., "body": ...}} using numbered headings."""
    sections: Dict[str, Dict[str, str]] = {}
    current: Optional[str] = None
    for line in full_text.splitlines():
        m = _HEADING_RE.match(line.strip())
        if m:
            current = m.group(1)
            sections[current] = {"title": m.group(2).strip(), "body": ""}
            continue
        if current:
            sections[current]["body"] += line + "\n"
    return sections


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #
def _body_to_blocks(body: str) -> List[Tuple[str, bool]]:
    """Turn wrapped PDF lines into logical blocks: [(text, is_equation)]."""
    blocks: List[Tuple[str, bool]] = []
    buf: List[str] = []

    def flush():
        if buf:
            blocks.append((" ".join(buf).strip(), False))
            buf.clear()

    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _EQUATION_RE.search(line):
            flush()
            blocks.append((line, True))
        else:
            buf.append(line)
    flush()
    return blocks


def _split_sentences(text: str) -> List[str]:
    # do not split after "et al." (citations such as "Rehman et al. (2023)")
    return [s.strip() for s in re.split(r"(?<!\bal\.)(?<=[.;])\s+(?=[A-Z(])", text) if s.strip()]


def chunk_text_blocks(blocks: List[Tuple[str, bool]], max_chars: int = MAX_CHARS) -> List[str]:
    """Pack paragraphs/sentences into chunks of <= max_chars. Equations are never split, and the
    last sentence of a chunk is repeated at the start of the next one (overlap)."""
    units: List[Tuple[str, bool]] = []
    i = 0
    while i < len(blocks):
        text, is_eq = blocks[i]
        # A lead-in sentence ending with ":" is kept together with the equation(s) that follow it.
        if (not is_eq and text.rstrip().endswith(":")
                and i + 1 < len(blocks) and blocks[i + 1][1]):
            sentences = _split_sentences(text)
            units.extend((s, False) for s in sentences[:-1])
            glued = [sentences[-1]]
            i += 1
            while i < len(blocks) and blocks[i][1]:
                glued.append(blocks[i][0])
                i += 1
            units.append(("\n".join(glued), True))
            continue
        if is_eq or len(text) <= max_chars:
            units.append((text, is_eq))
        else:
            units.extend((s, False) for s in _split_sentences(text))
        i += 1

    chunks: List[str] = []
    current: List[Tuple[str, bool]] = []
    size = 0
    for unit in units:
        if current and size + len(unit[0]) + 1 > max_chars:
            chunks.append("\n".join(t for t, _ in current))
            last = current[-1]
            if not last[1] and len(last[0]) <= OVERLAP_MAX_CHARS:
                current, size = [last], len(last[0])
            else:
                current, size = [], 0
        current.append(unit)
        size += len(unit[0]) + 1
    if current:
        chunks.append("\n".join(t for t, _ in current))
    return chunks


def _table_rows(tables: List[List[List[str]]]) -> List[List[str]]:
    """Find Table 1 (header: Assessment Dimension / Value / Penalty) and return its clean rows."""
    for table in tables:
        if table and table[0] and (table[0][0] or "").strip().lower().startswith("assessment dimension"):
            rows = []
            for row in table[1:]:
                cells = [re.sub(r"\s+", " ", (c or "").replace("\n", " ")).strip() for c in row]
                if any(cells):
                    rows.append(cells)
            return rows
    return []


def _table_chunks(rows: List[List[str]], raw_table_text: str, caption: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not rows:  # text-only reader: keep the raw table text as one chunk
        if raw_table_text.strip():
            out.append({"text": f"{caption}\n{raw_table_text.strip()}", "kind": "table"})
        return out

    whole = [caption, "Columns: Assessment Dimension | Value | Penalty (0 = best, 4 = worst)"]
    row_chunks = []
    for dim, values, penalties in (r[:3] for r in rows if len(r) >= 3):
        vals = [v.strip() for v in values.split("/")]
        pens = [p.strip() for p in penalties.split("/")]
        whole.append(f"{dim}: values {values} -> penalties {penalties}")
        if len(vals) == len(pens):
            mapping = "; ".join(f"{v} -> penalty {p}" for v, p in zip(vals, pens))
        else:
            mapping = f"values {values} -> penalties {penalties}"
        row_chunks.append(
            f"{caption}\nAssessment dimension: {dim}. Value-to-penalty mapping: {mapping}."
        )
    out.append({"text": "\n".join(whole), "kind": "table"})
    out.extend({"text": t, "kind": "table_row"} for t in row_chunks)
    return out


def build_chunks(pdf_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Read the PDF and return [{"id", "text", "metadata"}] ready for embedding."""
    pdf_path = pdf_path or find_pdf()
    full_text, tables = _read_pdf(pdf_path)
    sections = _split_sections(full_text)

    chunks: List[Dict[str, Any]] = []
    for number in INCLUDE_SECTIONS:
        if number not in sections:
            raise ValueError(f"Section {number} was not found in {pdf_path.name}.")
        title, body = sections[number]["title"], sections[number]["body"]
        header = f"[Methodology PDF, Section {number} - {title}]"

        # Split the section at the Table 1 caption (only section 3.2.2 contains it).
        lines = body.splitlines()
        cut = next((i for i, l in enumerate(lines) if _TABLE_CAPTION_RE.match(l.strip())), None)
        text_lines = lines if cut is None else lines[:cut]
        # drop the stray "Figure" placeholder line that precedes the table caption
        while text_lines and text_lines[-1].strip() in ("", "Figure"):
            text_lines.pop()

        for i, piece in enumerate(chunk_text_blocks(_body_to_blocks("\n".join(text_lines)))):
            chunks.append({"text": f"{header}\n{piece}", "kind": "text", "section": number})

        if cut is not None:
            caption = lines[cut].strip()
            raw_table = "\n".join(lines[cut + 1:])
            for t in _table_chunks(_table_rows(tables), raw_table, caption):
                t["text"] = f"{header}\n{t['text']}"
                t["section"] = number
                chunks.append(t)

    final = []
    for idx, c in enumerate(chunks):
        final.append({
            "id": f"method_{idx:03d}",
            "text": c["text"],
            "metadata": {
                "source": "Methodology_PDF",
                "section": c["section"],
                "kind": c["kind"],
                "file": pdf_path.name,
                "chunk": idx,
            },
        })
    return final


# --------------------------------------------------------------------------- #
# ChromaDB ingestion / retrieval
# --------------------------------------------------------------------------- #
def ingest_methodology() -> int:
    """Chunk the PDF, embed with Gemini and store in chroma_db/<methodology_rules>."""
    try:
        import chromadb
    except ImportError:
        raise ImportError("chromadb is not installed. Run: pip install chromadb")

    chunks = build_chunks()
    print(f">>> Methodology PDF: {len(chunks)} chunks "
          f"({sum(c['metadata']['kind'] == 'text' for c in chunks)} text, "
          f"{sum(c['metadata']['kind'] != 'text' for c in chunks)} table).")

    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(METHODOLOGY_COLLECTION)
        print(">>> Removed existing methodology collection (rebuilding).")
    except Exception:
        pass
    collection = client.create_collection(
        name=METHODOLOGY_COLLECTION,
        metadata={
            "description": "Standards/rules text and Table 1 from the Methodology PDF",
            "hnsw:space": "cosine",
        },
    )

    embedder = _embedder()
    batch = 50
    for i in range(0, len(chunks), batch):
        part = chunks[i:i + batch]
        vectors = embedder.embed_documents([c["text"] for c in part])
        collection.upsert(
            ids=[c["id"] for c in part],
            documents=[c["text"] for c in part],
            metadatas=[c["metadata"] for c in part],
            embeddings=vectors,
        )
    print(f">>> Successfully ingested {len(chunks)} methodology chunks into ChromaDB.")
    return len(chunks)


def query_methodology(query: str, n_results: int = 3) -> str:
    """Retrieve the most relevant methodology chunks for a question (query embeddings are cached)."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(DB_DIR))
        try:
            collection = client.get_collection(name=METHODOLOGY_COLLECTION)
        except Exception:
            return ("Methodology collection not built yet. "
                    "Run `python src/main.py --ingest-pdf` to create it.")
        q_vec, _ = _get_query_embedding(client, query)
        res = collection.query(query_embeddings=[q_vec], n_results=n_results)
        docs = res.get("documents", [[]])[0]
        return "\n---\n".join(docs) if docs else "No relevant methodology rules found."
    except Exception as e:
        return f"Methodology retrieval error: {e}"


if __name__ == "__main__":
    if "--preview" in sys.argv:
        for c in build_chunks():
            print(f"\n##### {c['id']}  ({c['metadata']['kind']}, {len(c['text'])} chars)")
            print(c["text"])
    else:
        ingest_methodology()