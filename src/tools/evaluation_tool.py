from scripts.evaluate_retrieval import build_result_summary, load_retriever
from src.evaluation.retrieval_eval import evaluate_results, load_eval_questions
from src.rerank.reranker import Reranker
import argparse

def evaluate_retrieval_tool(index_dir: str,eval_file: str,retriever: str = "bm25",top_k: int = 3,alpha: float = 0.3,rerank: bool = False,candidate_k: int = 10,) -> dict:

    if not index_dir:
        raise ValueError("index_dir must not be empty")
    if not eval_file:
        raise ValueError("eval_file must not be empty")
    if retriever not in {"dense", "bm25", "hybrid"}:
        raise ValueError(f"Unsupported retriever: {retriever}")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")
    if candidate_k <= 0:
        raise ValueError("candidate_k must be greater than 0")

    questions = load_eval_questions(eval_file)
    loaded_retriever = load_retriever(index_dir, retriever, alpha)

    reranker = None
    if rerank:
        reranker = Reranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    reports = []
    question_outputs = []

    for question in questions:
        query = question["query"]
        expected_pages = question["expected_pages"]

        retrieval_k = candidate_k if rerank else top_k
        results = loaded_retriever.search(query, top_k=retrieval_k)

        if reranker is not None:
            results = reranker.rerank(query, results, top_k=top_k)

        report = evaluate_results(results, expected_pages)
        reports.append(report)

        question_outputs.append(
            {
                "query": query,
                "expected_pages": report["expected_pages"],
                "retrieved_pages": report["retrieved_pages"],
                "hit": report["hit"],
                "recall": report["recall"],
                "mrr": report["mrr"],
                "results": [build_result_summary(result) for result in results],
            }
        )

    total = len(reports)
    mean_hit = sum(report["hit"] for report in reports) / total
    mean_recall = sum(report["recall"] for report in reports) / total
    mean_mrr = sum(report["mrr"] for report in reports) / total

    return {
        "config": {
            "index_dir": index_dir,
            "eval_file": eval_file,
            "retriever": retriever,
            "top_k": top_k,
            "alpha": alpha,
            "rerank": rerank,
            "candidate_k": candidate_k if rerank else None,
        },

        "overall": {
            "mean_hit": mean_hit,
            "mean_recall": mean_recall,
            "mean_mrr": mean_mrr,
        },

        "questions": question_outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test evaluation tool.")
    parser.add_argument("--index_dir", required=True, help="Directory of the built index.")
    parser.add_argument("--eval_file", required=True, help="Path to eval questions jsonl.")
    parser.add_argument(
        "--retriever",
        choices=["dense", "bm25", "hybrid"],
        default="bm25",
        help="Retriever backend.",
    )
    parser.add_argument("--top_k", type=int, default=3, help="Number of chunks to retrieve.")
    parser.add_argument("--alpha", type=float, default=0.3, help="Hybrid dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=10, help="Number of candidates before reranking.")

    args = parser.parse_args()

    result = evaluate_retrieval_tool(
        index_dir=args.index_dir,
        eval_file=args.eval_file,
        retriever=args.retriever,
        top_k=args.top_k,
        alpha=args.alpha,
        rerank=args.rerank,
        candidate_k=args.candidate_k,
    )

    print("Overall:")
    print(f"Mean Hit: {result['overall']['mean_hit']:.4f}")
    print(f"Mean Recall: {result['overall']['mean_recall']:.4f}")
    print(f"Mean MRR: {result['overall']['mean_mrr']:.4f}")

    print()
    print("Questions:")
    for question in result["questions"]:
        print(question["query"])
        print(f"  expected_pages: {question['expected_pages']}")
        print(f"  retrieved_pages: {question['retrieved_pages']}")
        print(f"  hit: {question['hit']}")
        print(f"  recall: {question['recall']:.4f}")
        print(f"  mrr: {question['mrr']:.4f}")


if __name__ == "__main__":
    main()