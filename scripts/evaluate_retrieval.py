import argparse
import json
from pathlib import Path

from src.config.config_loader import load_config
from src.embeddings.embedding_model import EmbeddingModel
from src.evaluation.retrieval_eval import evaluate_results,load_eval_questions
from src.index.bm25_index import BM25Index
from src.index.vector_store import VectorStore
from src.retrievers.hybrid_retriever import HybridRetriever
from src.rerank.reranker import Reranker


def load_retriever(index_dir: str, retriever_name: str, alpha: float):
    if retriever_name == "dense":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        store = VectorStore(model)
        store.load(index_dir)
        return store

    if retriever_name == "bm25":
        bm25_index = BM25Index()
        bm25_index.load(index_dir)
        return bm25_index

    if retriever_name == "hybrid":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        dense_store = VectorStore(model)
        dense_store.load(index_dir)

        bm25_index = BM25Index()
        bm25_index.load(index_dir)

        return HybridRetriever(
            dense_retriever=dense_store,
            bm25_retriever=bm25_index,
            alpha=alpha,
        )

    raise ValueError(f"Unknown retriever: {retriever_name}")


def print_retrieved_results(results: list[dict]) -> None:
    print("Retrieved results:")

    for rank, result in enumerate(results, start=1):
        score = result.get("score")
        rerank_score = result.get("rerank_score")

        score_text = ""
        if score is not None:
            score_text += f" score={score:.4f}"
        if rerank_score is not None:
            score_text += f" rerank={rerank_score:.4f}"

        print(
            f"[{rank}] page={result['page']} "
            f"chunk_id={result['chunk_id']}{score_text}"
        )
        print(result["text"][:300])
        print()


def build_result_summary(result: dict) -> dict:
    summary = {
        "chunk_id": result["chunk_id"],
        "source": result["source"],
        "page": result["page"],
        "text_preview": result["text"][:300],
    }

    if "score" in result:
        summary["score"] = result["score"]
    if "dense_score" in result:
        summary["dense_score"] = result["dense_score"]
    if "bm25_score" in result:
        summary["bm25_score"] = result["bm25_score"]
    if "rerank_score" in result:
        summary["rerank_score"] = result["rerank_score"]

    return summary


def save_eval_output(output_file: str, payload: dict) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def get_config_value(config: dict, section: str, key: str, default=None):
    if not config:
        return default

    section_config = config.get(section, {})

    if not isinstance(section_config, dict):
        return default

    return section_config.get(key, default)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--config", help="Path to YAML config file.")
    parser.add_argument("--index_dir", help="Directory of the built index.")
    parser.add_argument("--eval_file", help="Path to eval questions jsonl.")
    parser.add_argument("--retriever",choices=["dense", "bm25", "hybrid"],default=None,help="Retriever backend to evaluate.",)
    parser.add_argument("--top_k", type=int, default=None, help="Number of retrieved chunks.")
    parser.add_argument("--alpha", type=float, default=None, help="Hybrid retrieval dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=None, help="Number of candidates before reranking.")
    parser.add_argument("--reranker_model",default=None,help="Reranker model name.",)
    parser.add_argument("--show_results", action="store_true", help="Show retrieved chunk details.")
    parser.add_argument("--output_file", help="Optional path to save evaluation results as JSON.")

    args = parser.parse_args()

    config = {}
    if args.config:
        config = load_config(args.config)

    index_dir = args.index_dir or get_config_value(config, "index", "index_dir")
    eval_file = args.eval_file or get_config_value(config, "index", "eval_file")

    retriever_name = args.retriever or get_config_value(config, "retrieval", "retriever", "dense")
    top_k = args.top_k if args.top_k is not None else get_config_value(config, "retrieval", "top_k", 3)
    alpha = args.alpha if args.alpha is not None else get_config_value(config, "retrieval", "alpha", 0.5)

    rerank = args.rerank or get_config_value(config, "rerank", "enabled", False)
    candidate_k = (
        args.candidate_k
        if args.candidate_k is not None
        else get_config_value(config, "rerank", "candidate_k", 10)
    )
    reranker_model = args.reranker_model or get_config_value(
        config,
        "rerank",
        "model_name",
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
    )

    if not index_dir:
        raise ValueError("index_dir must be provided by --index_dir or config file")

    if not eval_file:
        raise ValueError("eval_file must be provided by --eval_file or config file")

    questions = load_eval_questions(eval_file)
    retriever = load_retriever(index_dir, retriever_name, alpha)

    reranker = None
    if rerank:
        reranker = Reranker(reranker_model)

    print(f"Rerank: {rerank}")
    if rerank:
        print(f"Candidate k: {candidate_k}")
        print(f"Reranker model: {reranker_model}")

    print(f"Index directory: {index_dir}")
    print(f"Eval file: {eval_file}")
    print(f"Retriever: {retriever_name}")
    print(f"Top k: {top_k}")
    print(f"Questions: {len(questions)}")
    print(f"Loaded retriever: {type(retriever).__name__}")
    print()

    reports = []
    question_outputs = []

    for i, question in enumerate(questions, start=1):
        query = question["query"]
        expected_pages = question["expected_pages"]

        retrieval_k = candidate_k if rerank else top_k
        results = retriever.search(query, top_k=retrieval_k)

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

        print(f"Question {i}: {query}")
        print(f"Expected pages: {report['expected_pages']}")
        print(f"Retrieved pages: {report['retrieved_pages']}")
        print(f"Hit: {report['hit']}")
        print(f"Recall: {report['recall']:.4f}")
        print(f"MRR: {report['mrr']:.4f}")

        if args.show_results:
            print_retrieved_results(results)

        print("-" * 80)

    total = len(reports)

    mean_hit = sum(report["hit"] for report in reports) / total
    mean_recall = sum(report["recall"] for report in reports) / total
    mean_mrr = sum(report["mrr"] for report in reports) / total

    print("Overall:")
    print(f"Mean Hit: {mean_hit:.4f}")
    print(f"Mean Recall: {mean_recall:.4f}")
    print(f"Mean MRR: {mean_mrr:.4f}")

    if args.output_file:
        payload = {
            "config": {
                "index_dir": index_dir,
                "eval_file": eval_file,
                "retriever": retriever_name,
                "top_k": top_k,
                "alpha": alpha,
                "rerank": rerank,
                "candidate_k": candidate_k if rerank else None,
                "reranker_model": reranker_model if rerank else None,
            },
            "overall": {
                "mean_hit": mean_hit,
                "mean_recall": mean_recall,
                "mean_mrr": mean_mrr,
            },
            "questions": question_outputs,
        }
        save_eval_output(args.output_file, payload)
        print(f"Saved evaluation results to: {args.output_file}")

if __name__ == "__main__":
    main()
