import os
import hashlib
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = ROOT_DIR / "chroma_db"
STANDARDS_DIR = ROOT_DIR / "Data" / "Standards"
COLLECTION_NAME = "water_standards"


def _embedder():
    """Gemini embeddings via the GOOGLE_API_KEY already used for the chat model."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model=_model_name(),
        google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
    )


def ingest_standards():
    """Ingests WHO and Pakistan NSDWQ CSV standards into ChromaDB using Gemini embeddings."""
    try:
        import chromadb
    except ImportError:
        raise ImportError("chromadb is not installed. Run: pip install chromadb")

    who_file = STANDARDS_DIR / "WHO_Drinking_Water_Quality_Standards.csv"
    nsdwq_file = STANDARDS_DIR / "Pakistan_NSDWQ_Standards_Sample_Parameters.csv"

    if not who_file.exists():
        raise FileNotFoundError(f"Missing WHO standards CSV at: {who_file}")
    if not nsdwq_file.exists():
        raise FileNotFoundError(f"Missing Pakistan NSDWQ CSV at: {nsdwq_file}")

    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Drop any old collection (e.g. built with MiniLM) so vector sizes can't clash.
    try:
        client.delete_collection(COLLECTION_NAME)
        print(">>> Removed existing collection (re-embedding with Gemini).")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "WHO & Pakistan NSDWQ Water Quality Standards",
            "hnsw:space": "cosine",
        },
    )

    ids, docs, metas = [], [], []

    print(">>> Reading WHO Standards...")
    who_df = pd.read_csv(who_file)
    for idx, row in who_df.iterrows():
        ids.append(f"who_{idx}")
        docs.append(
            f"Standard Agency: WHO\n"
            f"Parameter: {row.get('Parameter', '')} ({row.get('Chemical_Symbol_or_Formula', '')})\n"
            f"Guideline Value: {row.get('WHO_Guideline_Value', '')} {row.get('Unit', '')}\n"
            f"Health Significance: {row.get('Health_Implications_and_Significance', '')}\n"
            f"Sources: {row.get('Major_Sources', '')}\n"
            f"Guideline Notes: {row.get('WHO_Remarks_and_Notes', '')}"
        )
        metas.append({"param": str(row.get("Parameter", "")).lower(), "source": "WHO"})

    print(">>> Reading Pakistan NSDWQ Standards...")
    nsdwq_df = pd.read_csv(nsdwq_file)
    for idx, row in nsdwq_df.iterrows():
        ids.append(f"nsdwq_{idx}")
        docs.append(
            f"Standard Agency: Pakistan NSDWQ\n"
            f"Parameter: {row.get('Parameter', '')}\n"
            f"Permissible Limit: {row.get('Pakistan_NSDWQ_Limit', '')} {row.get('Unit', '')}\n"
            f"Notes: {row.get('Notes', '')}"
        )
        metas.append({"param": str(row.get("Parameter", "")).lower(), "source": "NSDWQ"})

    print(f">>> Embedding {len(docs)} documents with Gemini...")
    embedder = _embedder()
    batch = 50
    for i in range(0, len(docs), batch):
        vectors = embedder.embed_documents(docs[i:i + batch])
        collection.upsert(
            ids=ids[i:i + batch],
            documents=docs[i:i + batch],
            metadatas=metas[i:i + batch],
            embeddings=vectors,
        )

    print(f">>> Successfully ingested {len(who_df)} WHO and {len(nsdwq_df)} NSDWQ records into ChromaDB.")


def _model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")


def _query_cache_collection(client):
    """Persistent cache of query embeddings. One collection per embedding model,
    so changing EMBEDDING_MODEL never mixes vector sizes."""
    tag = hashlib.md5(_model_name().encode()).hexdigest()[:8]
    return client.get_or_create_collection(
        name=f"query_cache_{tag}", metadata={"hnsw:space": "cosine"}
    )


def _get_query_embedding(client, query: str):
    """Returns (vector, was_cached). Reuses a stored embedding if this query was asked before."""
    normalized = " ".join(query.lower().split())
    qid = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    cache = _query_cache_collection(client)

    try:
        hit = cache.get(ids=[qid], include=["embeddings"])
        embs = hit.get("embeddings")
        if embs is not None and len(embs) > 0:
            return [float(x) for x in embs[0]], True
    except Exception:
        pass  # cache problems must never break retrieval

    vec = _embedder().embed_query(query)
    try:
        cache.upsert(ids=[qid], documents=[normalized], embeddings=[vec])
    except Exception:
        pass
    return vec, False


def query_standards(query: str, n_results: int = 3) -> str:
    """Queries the water_standards collection; query embeddings are cached on disk."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(DB_DIR))
        collection = client.get_collection(name=COLLECTION_NAME)
        q_vec, cached = _get_query_embedding(client, query)
        print(f">>> Query embedding: {'loaded from cache' if cached else 'generated via Gemini and saved'}")
        res = collection.query(query_embeddings=[q_vec], n_results=n_results)
        docs = res.get("documents", [[]])[0]
        return "\n---\n".join(docs) if docs else "No relevant standards found."
    except Exception as e:
        return f"Standards retrieval error: {e}"


if __name__ == "__main__":
    ingest_standards()