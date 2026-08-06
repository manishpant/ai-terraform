"""
Convenience entry: python -m src.rag.ingest
"""

from src.rag.retriever import build_index, INDEX_DIR


def main() -> None:
    print("Ingesting knowledge/ into FAISS ...")
    build_index()
    print(f"Done. Index at {INDEX_DIR}")


if __name__ == "__main__":
    main()
