#在线查询检索，负责查询已经建好的索引
import argparse
from src.embeddings.embedding_model import EmbeddingModel
from src.index.vector_store import VectorStore
from src.llm.vllm_client import MockLLMClient, VLLMClient
from src.index.bm25_index import BM25Index
from src.retrievers.hybrid_retriever import HybridRetriever
from src.rerank.reranker import Reranker
from src.evaluation.citation_eval import check_citations

def build_context(results: list[dict]) -> str:
    context_parts = []

    for i, result in enumerate(results, start=1):
        context_parts.append(
            "[{index}] source={source}, page={page}, chunk_id={chunk_id}\n{text}".format(
                index=i,
                source=result["source"],
                page=result["page"],
                chunk_id=result["chunk_id"],
                text=result["text"],
            )
        )
    return "\n\n".join(context_parts)


def build_prompt(query: str, context: str) -> str:
    return f"""You are a research paper reading assistant.

Use only the provided context to answer the question.

Rules:
- Every sentence in the answer must end with one or more citation markers, such as [1] or [1][2].
- Only use citation numbers that appear in the provided context.
- If the context does not contain enough information, answer exactly: The provided context is insufficient.
- Do not invent citations.
- Do not include a separate references section.

Required output format:
 <your answer with citation markers>

Example:
Question:
What does the paper propose?

Answer:
The paper proposes a new uncertainty-aware diagnosis method [1].

Context:
{context}

Question:
{query}

Answer:
"""

def print_sources(results: list[dict]) -> None:
    print("Sources:")
    for i, result in enumerate(results, start=1):
        print(
            f"[{i}] {result['source']}, "
            f"page {result['page']}, "
            f"chunk_id={result['chunk_id']}"
        )

def print_citation_check(report: dict) -> None:
    print("Citation Check:")
    print(f"has_citations: {report['has_citations']}")
    print(f"used_citations: {report['used_citations']}")
    print(f"invalid_citations: {report['invalid_citations']}")
    print(f"source_count: {report['source_count']}")
    print(f"is_valid: {report['is_valid']}")

    if report["warnings"]:
        print("warnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run retrieval over a built vector index.")
    parser.add_argument("--index_dir", required=True, help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="User question.")
    parser.add_argument("--top_k", type=int, default=5, help="Number of chunks to retrieve.")
    parser.add_argument("--llm", choices=["mock", "vllm"], default="mock", help="LLM backend to use.")
    parser.add_argument("--base_url", default="http://localhost:7890/v1", help="OpenAI-compatible API base URL.")
    parser.add_argument("--api_key", default="abc123", help="API key for the LLM service.")
    parser.add_argument("--model_name", default="X", help="Model name served by vLLM.")
    parser.add_argument("--temperature", type=float, default=0.2, help="LLM sampling temperature.")
    parser.add_argument("--max_tokens", type=int, default=128, help="Maximum tokens for LLM output.")
    parser.add_argument("--retriever",choices=["dense", "bm25", "hybrid"],default="dense",help="Retriever backend to use.",)
    parser.add_argument("--alpha", type=float, default=0.5, help="Hybrid retrieval dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=20, help="Number of candidates before reranking.")
    parser.add_argument("--reranker_model", default="cross-encoder/ms-marco-MiniLM-L-6-v2", help="Reranker model name.")
    parser.add_argument("--check_citations",action="store_true",help="Check whether the generated answer contains valid citation markers.",)
    
    args = parser.parse_args()

    print(f"Index directory: {args.index_dir}")
    print(f"Query: {args.query}")
    print(f"Top k: {args.top_k}")

    if args.retriever == "dense":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        store = VectorStore(model)
        store.load(args.index_dir)
        retrieval_k = args.candidate_k if args.rerank else args.top_k
        results = store.search(args.query, top_k=retrieval_k)
        if args.rerank:
            reranker = Reranker(args.reranker_model)
            results = reranker.rerank(args.query, results, top_k=args.top_k)
    elif args.retriever == "bm25":
        bm25_index = BM25Index()
        bm25_index.load(args.index_dir)
        retrieval_k = args.candidate_k if args.rerank else args.top_k
        results = bm25_index.search(args.query, top_k=retrieval_k)
        if args.rerank:
            reranker = Reranker(args.reranker_model)
            results = reranker.rerank(args.query, results, top_k=args.top_k)
    else:
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        dense_store = VectorStore(model)
        dense_store.load(args.index_dir)
        bm25_index = BM25Index()
        bm25_index.load(args.index_dir)
        hybrid_retriever = HybridRetriever(dense_retriever=dense_store,bm25_retriever=bm25_index,alpha=args.alpha,)
        retrieval_k = args.candidate_k if args.rerank else args.top_k
        results = hybrid_retriever.search(args.query, top_k=retrieval_k)
        if args.rerank:
            reranker = Reranker(args.reranker_model)
            results = reranker.rerank(args.query, results, top_k=args.top_k)

    context = build_context(results)
    #print("Context:")
    #print(context[:2000])

    prompt = build_prompt(args.query, context)
    #print("Prompt:")
    #print(prompt[:3000])


    if args.llm == "mock":
        llm = MockLLMClient()
    else:
        llm = VLLMClient(base_url=args.base_url,api_key=args.api_key,model_name=args.model_name,)
        
    answer = llm.generate(prompt, temperature=args.temperature,max_tokens=args.max_tokens,)

    print("Question:")
    print(args.query)
    print()

    print("Answer:")
    print(answer)
    print()

    print_sources(results)
    print()

    if args.check_citations:
        citation_report = check_citations(answer, results)
        print_citation_check(citation_report)
        print()

    print("Retrieved chunks:")
    for result in results:
        score_info = f"[score={result['score']:.4f}]"

        if "dense_score" in result and "bm25_score" in result:
            score_info = (
                f"[score={result['score']:.4f} "
                f"dense={result['dense_score']:.4f} "
                f"bm25={result['bm25_score']:.4f}]"
            )

        if "rerank_score" in result:
            score_info += f" rerank={result['rerank_score']:.4f}"

        print(
            f"{score_info} "
            f"{result['source']} page={result['page']} "
            f"chunk_id={result['chunk_id']}"
        )
        
        print(result["text"][:500])
        print("-" * 80)

if __name__ == "__main__":
    main()
