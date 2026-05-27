from pathlib import Path
import argparse
import sys
import pymupdf


def load_pdf(pdf_path: str) -> list[dict]:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not path.is_file():
        raise ValueError(f"PDF path is not a file: {pdf_path}")

    try:
        pdf = pymupdf.open(path)
    except Exception as exc:
        raise ValueError(f"Failed to open PDF: {pdf_path}") from exc

    documents = []

    try:
        for page_index in range(pdf.page_count):
            page = pdf[page_index]
            text = page.get_text("text").strip()

            if not text:
                continue

            document = {
                "text": text,
                "source": pdf_path,
                "page": page_index + 1,
                "metadata": {"type": "pdf"},
            }

            documents.append(document)
    finally:
        pdf.close()

    if not documents:
        raise ValueError(
            f"No extractable text found in PDF: {pdf_path}. "
            "Scanned PDFs require OCR, which is not supported yet."
        )

    return documents

def main() -> None:
    parser = argparse.ArgumentParser(description="Load a PDF and preview extracted text.")
    parser.add_argument("pdf_path", help="Path to the PDF file.")

    args = parser.parse_args()

    try:
        documents = load_pdf(args.pdf_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Loaded {len(documents)} pages with extractable text.")

    for document in documents[:5]:
        text_preview = document["text"][:120].replace("\n", " ")
        print(
            f"page={document['page']} \n"
            f"source={document['source']} \n"
            f"metadata={document['metadata']} \n"
            f"text={text_preview}...\n"
        )


if __name__ == "__main__":
    main()