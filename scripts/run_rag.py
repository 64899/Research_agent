#在线查询检索，负责查询已经建好的索引
import argparse
import sys
from src.embeddings.embedding_model import EmbeddingModel
from src.index.vector_store import VectorStore
from src.llm.vllm_client import MockLLMClient, VLLMClient
from src.index.bm25_index import BM25Index
from src.retrievers.hybrid_retriever import HybridRetriever
from src.rerank.reranker import Reranker
from src.evaluation.citation_eval import check_citations
from src.config.config_loader import load_config

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

def safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    safe_text = str(text).encode(encoding, errors="replace").decode(encoding)
    print(safe_text)

def get_config_value(config: dict, section: str, key: str, default=None):
    if not config:
        return default

    section_config = config.get(section, {})

    if not isinstance(section_config, dict):
        return default

    return section_config.get(key, default)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run retrieval over a built vector index.")
    parser.add_argument("--index_dir", help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="User question.")
    parser.add_argument("--top_k", type=int, default=None, help="Number of chunks to retrieve.")
    parser.add_argument("--llm", choices=["mock", "vllm"], default=None, help="LLM backend to use.")
    parser.add_argument("--base_url", default=None, help="OpenAI-compatible API base URL.")
    parser.add_argument("--api_key", default=None, help="API key for the LLM service.")
    parser.add_argument("--model_name", default=None, help="Model name served by vLLM.")
    parser.add_argument("--temperature", type=float, default=None, help="LLM sampling temperature.")
    parser.add_argument("--max_tokens", type=int, default=None, help="Maximum tokens for LLM output.")
    parser.add_argument("--retriever", choices=["dense", "bm25", "hybrid"], default=None, help="Retriever backend to use.")
    parser.add_argument("--alpha", type=float, default=None, help="Hybrid retrieval dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=None, help="Number of candidates before reranking.")
    parser.add_argument("--reranker_model", default=None, help="Reranker model name.")
    parser.add_argument("--check_citations",action="store_true",help="Check whether the generated answer contains valid citation markers.",)
    parser.add_argument("--config", help="Path to YAML config file.")
    
    args = parser.parse_args()
    config = {}
    if args.config:
        config = load_config(args.config)

    query = args.query
    index_dir = args.index_dir or get_config_value(config, "index", "index_dir")

    retriever = args.retriever or get_config_value(config, "retrieval", "retriever", "dense")
    top_k = args.top_k if args.top_k is not None else get_config_value(config, "retrieval", "top_k", 5)
    alpha = args.alpha if args.alpha is not None else get_config_value(config, "retrieval", "alpha", 0.5)

    rerank = args.rerank or get_config_value(config, "rerank", "enabled", False)
    candidate_k = (
        args.candidate_k
        if args.candidate_k is not None
        else get_config_value(config, "rerank", "candidate_k", 20)
    )
    reranker_model = args.reranker_model or get_config_value(
        config,
        "rerank",
        "model_name",
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
    )

    llm = args.llm or get_config_value(config, "llm", "provider", "mock")
    base_url = args.base_url or get_config_value(config, "llm", "base_url", "http://localhost:7890/v1")
    api_key = args.api_key or get_config_value(config, "llm", "api_key", "abc123")
    model_name = args.model_name or get_config_value(config, "llm", "model_name", "X")
    temperature = (
        args.temperature
        if args.temperature is not None
        else get_config_value(config, "llm", "temperature", 0.2)
    )
    max_tokens = (
        args.max_tokens
        if args.max_tokens is not None
        else get_config_value(config, "llm", "max_tokens", 128)
    )

    if not index_dir:
        raise ValueError("index_dir must be provided by --index_dir or config file")

    print(f"Index directory: {index_dir}")
    print(f"Query: {query}")
    print(f"Top k: {top_k}")

    if retriever == "dense":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        store = VectorStore(model)
        store.load(index_dir)
        retrieval_k = candidate_k if rerank else top_k
        results = store.search(query, top_k=retrieval_k)
        if rerank:
            reranker = Reranker(reranker_model)
            results = reranker.rerank(query, results, top_k=top_k)
    elif retriever == "bm25":
        bm25_index = BM25Index()
        bm25_index.load(index_dir)
        retrieval_k = candidate_k if rerank else top_k
        results = bm25_index.search(query, top_k=retrieval_k)
        if rerank:
            reranker = Reranker(reranker_model)
            results = reranker.rerank(query, results, top_k=top_k)
    else:
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        dense_store = VectorStore(model)
        dense_store.load(index_dir)
        bm25_index = BM25Index()
        bm25_index.load(index_dir)
        hybrid_retriever = HybridRetriever(dense_retriever=dense_store,bm25_retriever=bm25_index,alpha=alpha,)
        retrieval_k = candidate_k if rerank else top_k
        results = hybrid_retriever.search(query, top_k=retrieval_k)
        if rerank:
            reranker = Reranker(reranker_model)
            results = reranker.rerank(query, results, top_k=top_k)

    context = build_context(results)
    #print("Context:")
    #print(context[:2000])

    prompt = build_prompt(query, context)
    #print("Prompt:")
    #print(prompt[:3000])


    if llm == "mock":
        llm_client = MockLLMClient()
    else:
        llm_client = VLLMClient(
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
        )
        
    answer = llm_client.generate(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    print("Question:")
    print(query)
    print()

    print("Answer:")
    safe_print(answer)
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
        
        safe_print(result["text"][:500])
        print("-" * 80)

if __name__ == "__main__":
    main()
