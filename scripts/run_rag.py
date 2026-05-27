#在线查询检索，负责查询已经建好的索引
import argparse
from src.embeddings.embedding_model import EmbeddingModel
from src.index.vector_store import VectorStore
from src.llm.vllm_client import MockLLMClient

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

    args = parser.parse_args()

    print(f"Index directory: {args.index_dir}")
    print(f"Query: {args.query}")
    print(f"Top k: {args.top_k}")

    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")

    store = VectorStore(model)
    store.load(args.index_dir)

    results = store.search(args.query, top_k=args.top_k)

    context = build_context(results)
    #print("Context:")
    #print(context[:2000])

    prompt = build_prompt(args.query, context)
    #print("Prompt:")
    #print(prompt[:3000])

    llm = MockLLMClient()
    answer = llm.generate(prompt)

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
        print(
            f"[score={result['score']:.4f}] "
            f"{result['source']} page={result['page']} "
            f"chunk_id={result['chunk_id']}"
        )
        print(result["text"][:500])
        print("-" * 80)

if __name__ == "__main__":
    main()