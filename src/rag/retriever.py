"""
RAG = Retrieval-Augmented Generation.

Plain idea:
  1) Split knowledge docs into chunks
  2) Turn chunks into vectors (embeddings) and store in FAISS
  3) At question time, find similar chunks
  4) Stuff those chunks into the LLM prompt so answers are grounded

This is NOT magic memory — it's search + LLM.
"""

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
INDEX_DIR = REPO_ROOT / "rag_index"


def build_index() -> FAISS:
    """Load knowledge/*.md, split, embed, save FAISS index to disk."""
    if not KNOWLEDGE_DIR.exists():
        raise FileNotFoundError(f"Missing {KNOWLEDGE_DIR}")

    loader = DirectoryLoader(
        str(KNOWLEDGE_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    if not docs:
        raise RuntimeError("No markdown documents found in knowledge/")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    splits = splitter.split_documents(docs)

    # Local embeddings — no Anthropic credit needed for vectors
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = FAISS.from_documents(splits, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(INDEX_DIR))
    return store


def load_index() -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    if not INDEX_DIR.exists():
        return build_index()
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,  # local PoC index you built yourself
    )


def retrieve(query: str, k: int = 5) -> str:
    """Return top-k chunks with source metadata for citations."""
    store = load_index()
    hits = store.similarity_search(query, k=k)
    if not hits:
        return "No relevant knowledge found."
    parts: list[str] = []
    for i, doc in enumerate(hits, start=1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    print("Building RAG index from knowledge/ ...")
    build_index()
    print(f"Saved index to {INDEX_DIR}")
    print("--- sample retrieve ---")
    print(retrieve("terraform formatting and pull request policy"))
