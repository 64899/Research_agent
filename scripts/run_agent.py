import argparse

from src.agent.research_agent import ResearchAgent, print_agent_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ResearchAgent.")
    parser.add_argument("--index_dir", required=True, help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="User input.")
    parser.add_argument("--eval_file", help="Path to eval questions jsonl.")

    parser.add_argument(
        "--retriever",
        choices=["dense", "bm25", "hybrid"],
        default="bm25",
        help="Retriever backend.",
    )
    parser.add_argument("--top_k", type=int, default=3, help="Number of chunks.")
    parser.add_argument("--alpha", type=float, default=0.3, help="Hybrid dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=10, help="Number of candidates before reranking.")

    parser.add_argument("--llm", choices=["mock", "vllm"], default="mock", help="LLM backend.")
    parser.add_argument("--base_url", default="http://localhost:7890/v1", help="OpenAI-compatible API base URL.")
    parser.add_argument("--api_key", default="abc123", help="API key for vLLM.")
    parser.add_argument("--model_name", default="X", help="Model name served by vLLM.")

    args = parser.parse_args()

    agent = ResearchAgent(
        index_dir=args.index_dir,
        eval_file=args.eval_file,
        retriever=args.retriever,
        top_k=args.top_k,
        alpha=args.alpha,
        rerank=args.rerank,
        candidate_k=args.candidate_k,
        llm=args.llm,
        base_url=args.base_url,
        api_key=args.api_key,
        model_name=args.model_name,
    )

    result = agent.run(args.query)
    print_agent_result(result)


if __name__ == "__main__":
    main()