from src.tools.retrieval_tool import retrieve_chunks
from src.llm.vllm_client import MockLLMClient, VLLMClient
import argparse

def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            "[{index}] source={source}, page={page}, chunk_id={chunk_id}\n{text}".format(
                index=i,
                source=chunk["source"],
                page=chunk["page"],
                chunk_id=chunk["chunk_id"],
                text=chunk["text"],
            )
        )

    return "\n\n".join(context_parts)


def build_prompt(query: str, context: str) -> str:
    return f"""You are a research paper reading assistant.

Use only the provided context to answer the question.
If the context does not contain enough information, say that the provided context is insufficient.

Context:
{context}

Question:
{query}

Answer:
"""


def answer_question(
    index_dir: str,
    query: str,
    retriever: str = "bm25",
    top_k: int = 3,
    alpha: float = 0.3,
    rerank: bool = False,
    candidate_k: int = 10,
    llm: str = "mock",
    base_url: str = "http://localhost:7890/v1",
    api_key: str = "abc123",
    model_name: str = "X",
    temperature: float = 0.1,
    max_tokens: int = 192,
) -> dict:
    
    if not index_dir:
        raise ValueError("index_dir must not be empty")
    if not query:
        raise ValueError("query must not be empty")
    if llm not in {"mock", "vllm"}:
        raise ValueError(f"Unsupported llm: {llm}")

    chunks = retrieve_chunks(
        index_dir=index_dir,
        query=query,
        retriever=retriever,
        top_k=top_k,
        alpha=alpha,
        rerank=rerank,
        candidate_k=candidate_k,
    )

    context = build_context(chunks)
    prompt = build_prompt(query, context)
    if llm == "mock":
        llm_client = MockLLMClient()
        answer = llm_client.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
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
    
    return {
        "question": query,
        "answer": answer,
        "sources": chunks,
        "context": context,
        "prompt": prompt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG tool.")
    parser.add_argument("--index_dir", required=True, help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="User question.")
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
    parser.add_argument("--llm", choices=["mock", "vllm"], default="mock", help="LLM backend.")
    parser.add_argument("--base_url", default="http://localhost:7890/v1", help="OpenAI-compatible API base URL.")
    parser.add_argument("--api_key", default="abc123", help="API key for vLLM.")
    parser.add_argument("--model_name", default="X", help="Model name served by vLLM.")
    parser.add_argument("--temperature", type=float, default=0.1, help="LLM temperature.")
    parser.add_argument("--max_tokens", type=int, default=192, help="Maximum LLM output tokens.")

    args = parser.parse_args()

    result = answer_question(
        index_dir=args.index_dir,
        query=args.query,
        retriever=args.retriever,
        top_k=args.top_k,
        alpha=args.alpha,
        rerank=args.rerank,
        candidate_k=args.candidate_k,
        llm=args.llm,
        base_url=args.base_url,
        api_key=args.api_key,
        model_name=args.model_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    print("Question:")
    print(result["question"])
    print()

    print("Answer:")
    print(result["answer"])
    print()

    print("Sources:")
    for i, source in enumerate(result["sources"], start=1):
        print(
            f"[{i}] {source['source']}, "
            f"page {source['page']}, "
            f"chunk_id={source['chunk_id']}"
        )


if __name__ == "__main__":
    main()