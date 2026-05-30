from src.embeddings.embedding_model import EmbeddingModel
from src.index.bm25_index import BM25Index
from src.index.vector_store import VectorStore
from src.rerank.reranker import Reranker
from src.retrievers.hybrid_retriever import HybridRetriever
import argparse
import logging

def load_retriever(index_dir: str, retriever: str, alpha: float):
    if retriever == "dense":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        store = VectorStore(model)
        store.load(index_dir)
        return store

    if retriever == "bm25":
        bm25_index = BM25Index()
        bm25_index.load(index_dir)
        return bm25_index

    if retriever == "hybrid":
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

    raise ValueError(f"Unsupported retriever: {retriever}")

def retrieve_chunks(index_dir: str,query: str,retriever: str = "bm25",top_k: int = 3,alpha: float = 0.3,rerank: bool = False,candidate_k: int = 10,logger: logging.Logger | None = None,) -> list[dict]:
    if not index_dir:
        raise ValueError("index_dir must not be empty")

    if not query:
        raise ValueError("query must not be empty")

    if retriever not in {"dense", "bm25", "hybrid"}:
        raise ValueError(f"Unsupported retriever: {retriever}")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    if candidate_k <= 0:
        raise ValueError("candidate_k must be greater than 0")
    
    logger = logger or logging.getLogger(__name__)
    logger.info("retrieval_tool_started")
    logger.info(
        "retrieval_config: "
        f"retriever={retriever}, "
        f"top_k={top_k}, "
        f"alpha={alpha}, "
        f"rerank={rerank}, "
        f"candidate_k={candidate_k}"
    )

    loaded_retriever = load_retriever(index_dir, retriever, alpha)

    retrieval_k = candidate_k if rerank else top_k
    results = loaded_retriever.search(query, top_k=retrieval_k)

    if rerank:
        reranker = Reranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
        results = reranker.rerank(query, results, top_k=top_k)
    
    logger.info(f"retrieval_finished results={len(results)}")
    return results

def main() -> None:
    parser = argparse.ArgumentParser(description="Test retrieval tool.")
    parser.add_argument("--index_dir", required=True, help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="Search query.")
    parser.add_argument(
        "--retriever",
        choices=["dense", "bm25", "hybrid"],
        default="bm25",
        help="Retriever backend.",
    )
    parser.add_argument("--top_k", type=int, default=3, help="Number of chunks to return.")
    parser.add_argument("--alpha", type=float, default=0.3, help="Hybrid dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=10, help="Number of candidates before reranking.")

    args = parser.parse_args()

    results = retrieve_chunks(
        index_dir=args.index_dir,
        query=args.query,
        retriever=args.retriever,
        top_k=args.top_k,
        alpha=args.alpha,
        rerank=args.rerank,
        candidate_k=args.candidate_k,
    )

    print(f"Retrieved chunks: {len(results)}")

    for result in results:
        score_text = f"score={result['score']:.4f}"
        if "rerank_score" in result:
            score_text += f" rerank={result['rerank_score']:.4f}"

        print(
            f"{result['chunk_id']} "
            f"page={result['page']} "
            f"{score_text}"
        )
        print(result["text"][:300])
        print("-" * 80)


if __name__ == "__main__":
    main()