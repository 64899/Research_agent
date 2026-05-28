import json
from pathlib import Path


def load_eval_questions(path: str) -> list[dict]:
    eval_path = Path(path)

    if not eval_path.exists():
        raise FileNotFoundError(f"Eval questions file not found: {path}")

    if not eval_path.is_file():
        raise ValueError(f"Eval questions path is not a file: {path}")

    questions = []

    with eval_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            item = json.loads(line)

            if "query" not in item:
                raise ValueError(f"Missing query at line {line_number}")

            if "expected_pages" not in item:
                raise ValueError(f"Missing expected_pages at line {line_number}")

            questions.append(item)

    if not questions:
        raise ValueError(f"No eval questions found in: {path}")

    return questions

def hit_at_k(results: list[dict], expected_pages: list[int]) -> int:
    expected_page_set = set(expected_pages)

    for result in results:
        if result["page"] in expected_page_set:
            return 1

    return 0

def recall_at_k(results: list[dict], expected_pages: list[int]) -> float:
    expected_page_set = set(expected_pages)

    if not expected_page_set:
        return 0.0

    retrieved_pages = set()

    for result in results:
        retrieved_pages.add(result["page"])

    hit_pages = expected_page_set.intersection(retrieved_pages)

    return len(hit_pages) / len(expected_page_set)

def reciprocal_rank(results: list[dict], expected_pages: list[int]) -> float:
    expected_page_set = set(expected_pages)

    for rank, result in enumerate(results, start=1):
        if result["page"] in expected_page_set:
            return 1.0 / rank

    return 0.0

def evaluate_results(results: list[dict], expected_pages: list[int]) -> dict:
    return {
        "hit": hit_at_k(results, expected_pages),
        "recall": recall_at_k(results, expected_pages),
        "mrr": reciprocal_rank(results, expected_pages),
        "expected_pages": expected_pages,
        "retrieved_pages": [result["page"] for result in results],
    }