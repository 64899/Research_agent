from pathlib import Path
import re

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _build_chunk_id(source: str, page: int | None, index: int) -> str:
    source_name = Path(source).stem
    page_part = f"p{page}" if page is not None else "pNA"
    return f"{source_name}_{page_part}_c{index}"

def chunk_documents(documents: list[dict],chunk_size: int = 800,overlap: int = 100,min_chunk_chars: int = 200,) -> list[dict]:
    
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    if min_chunk_chars < 0:
        raise ValueError("min_chunk_chars must be greater than or equal to 0")

    chunks = []
    step = chunk_size - overlap

    for document in documents:
        text = document["text"]

        for start in range(0, len(text), step):
            end = start + chunk_size
            chunk_text = _normalize_text(text[start:end])
            
            if len(chunk_text) < min_chunk_chars:
                continue
            
            chunks.append(
                {
                    "chunk_id":_build_chunk_id(document["source"],document["page"],len(chunks),),
                    "text": chunk_text,
                    "source": document["source"],
                    "page": document["page"],
                    "metadata": dict(document.get("metadata", {})),
                }
            )

    return chunks

def main() -> None:
    documents = [
        {
            "text": "abcdefghijklmnopqrstuvwxyz",
            "source": "demo.txt",
            "page": 1,
            "metadata": {"type": "demo"},
        }
    ]

    chunks = chunk_documents(documents, chunk_size=10, overlap=2)

    print(f"Created {len(chunks)} chunks.")

    for chunk in chunks:
        print(
            f"{chunk['chunk_id']} "
            f"page={chunk['page']} "
            f"text={chunk['text']}"
        )


if __name__ == "__main__":
    main()