#在线查询检索，负责查询已经建好的索引
import argparse
from src.embeddings.embedding_model import EmbeddingModel
from src.index.vector_store import VectorStore
from src.llm.vllm_client import MockLLMClient, VLLMClient
from src.index.bm25_index import BM25Index
from src.retrievers.hybrid_retriever import HybridRetriever

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

Answer the question based only on the provided context.
If the context does not contain enough evidence, say that the document does not provide enough evidence.
Do not invent facts.
Include citation markers like [1], [2] when using evidence from the context.

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

    args = parser.parse_args()

    print(f"Index directory: {args.index_dir}")
    print(f"Query: {args.query}")
    print(f"Top k: {args.top_k}")

    if args.retriever == "dense":
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        store = VectorStore(model)
        store.load(args.index_dir)
        results = store.search(args.query, top_k=args.top_k)
    elif args.retriever == "bm25":
        bm25_index = BM25Index()
        bm25_index.load(args.index_dir)
        results = bm25_index.search(args.query, top_k=args.top_k)
    else:
        model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")
        dense_store = VectorStore(model)
        dense_store.load(args.index_dir)
        bm25_index = BM25Index()
        bm25_index.load(args.index_dir)
        hybrid_retriever = HybridRetriever(dense_retriever=dense_store,bm25_retriever=bm25_index,alpha=args.alpha,)
        results = hybrid_retriever.search(args.query, top_k=args.top_k)

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

    print("Retrieved chunks:")
    for result in results:
        score_info = f"[score={result['score']:.4f}]"
        if "dense_score" in result and "bm25_score" in result:
            score_info = (f"[score={result['score']:.4f} "f"dense={result['dense_score']:.4f} "f"bm25={result['bm25_score']:.4f}]")
        print(
    f"{score_info} "
    f"{result['source']} page={result['page']} "
    f"chunk_id={result['chunk_id']}")
        print(result["text"][:500])
        print("-" * 80)

if __name__ == "__main__":
    main()