import re

def extract_citation_numbers(answer: str) -> list[int]:
    matches = re.findall(r"\[(\d+)\]", answer)
    return [int(match) for match in matches]

def check_citations(answer: str, sources: list[dict]) -> dict:

    if not isinstance(answer, str):
        raise TypeError("answer must be a string")
    if not isinstance(sources, list):
        raise TypeError("sources must be a list of dictionaries")
    for source in sources:
        if not isinstance(source, dict):
            raise TypeError("each source must be a dictionary")
    
    source_count = len(sources)

    used_citations = extract_citation_numbers(answer)
    unique_used_citations = sorted(set(used_citations))

    invalid_citations = []
    for citation in unique_used_citations:
        if citation < 1 or citation > source_count:
            invalid_citations.append(citation)
    
    warnings = []
    if not unique_used_citations:
        warnings.append("answer does not contain citation markers like [1]")
    if invalid_citations:
        warnings.append("answer contains citation markers outside the available source range")
    if source_count == 0:
        warnings.append("no sources were provided")

    return {
        "has_citations": bool(unique_used_citations),
        "used_citations": unique_used_citations,
        "invalid_citations": invalid_citations,
        "source_count": source_count,
        "is_valid": bool(unique_used_citations) and not invalid_citations,
        "warnings": warnings,
    }

def main() -> None:
    sources = [
        {"source": "paper.pdf", "page": 1, "chunk_id": "c1"},
        {"source": "paper.pdf", "page": 2, "chunk_id": "c2"},
    ]

    examples = [
        "The method is DVAN [1].",
        "The method is DVAN [3].",
        "The method is DVAN.",
    ]

    for answer in examples:
        print("Answer:")
        print(answer)
        print("Citation Check:")
        print(check_citations(answer, sources))
        print("-" * 80)


if __name__ == "__main__":
    main()