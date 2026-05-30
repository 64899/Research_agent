import argparse
from src.utils.logger import setup_logger
from src.agent.research_agent import ResearchAgent, print_agent_result
from src.config.config_loader import load_config

def get_config_value(config: dict, section: str, key: str, default=None):
    if not config:
        return default

    section_config = config.get(section, {})

    if not isinstance(section_config, dict):
        return default

    return section_config.get(key, default)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run ResearchAgent.")
    parser.add_argument("--index_dir", help="Directory of the built index.")
    parser.add_argument("--query", required=True, help="User input.")
    parser.add_argument("--eval_file", help="Path to eval questions jsonl.")

    parser.add_argument("--retriever", choices=["dense", "bm25", "hybrid"], default=None, help="Retriever backend.")
    parser.add_argument("--top_k", type=int, default=None, help="Number of chunks.")
    parser.add_argument("--alpha", type=float, default=None, help="Hybrid dense weight.")
    parser.add_argument("--rerank", action="store_true", help="Enable reranking.")
    parser.add_argument("--candidate_k", type=int, default=None, help="Number of candidates before reranking.")
    parser.add_argument("--llm", choices=["mock", "vllm"], default=None, help="LLM backend.")
    parser.add_argument("--base_url", default=None, help="OpenAI-compatible API base URL.")
    parser.add_argument("--api_key", default=None, help="API key for vLLM.")
    parser.add_argument("--model_name", default=None, help="Model name served by vLLM.")
    parser.add_argument("--temperature", type=float, default=None, help="Temperature for LLM sampling.")
    parser.add_argument("--max_tokens", type=int, default=None, help="Maximum number of tokens for LLM generation.")
    parser.add_argument("--config", help="Path to YAML config file.")

    args = parser.parse_args()

    config = {}
    if args.config:
        config = load_config(args.config)
    

    index_dir = args.index_dir or get_config_value(config, "index", "index_dir")
    eval_file = args.eval_file or get_config_value(config, "index", "eval_file")
    retriever = args.retriever or get_config_value(config, "retrieval", "retriever", "bm25")
    top_k = args.top_k if args.top_k is not None else get_config_value(config, "retrieval", "top_k", 3)
    alpha = args.alpha if args.alpha is not None else get_config_value(config, "retrieval", "alpha", 0.3)
    rerank = args.rerank or get_config_value(config, "rerank", "enabled", False)
    candidate_k = (
        args.candidate_k
        if args.candidate_k is not None
        else get_config_value(config, "rerank", "candidate_k", 10)
    )
    llm = args.llm or get_config_value(config, "llm", "provider", "mock")
    base_url = args.base_url or get_config_value(config, "llm", "base_url", "http://localhost:7890/v1")
    api_key = args.api_key or get_config_value(config, "llm", "api_key", "abc123")
    model_name = args.model_name or get_config_value(config, "llm", "model_name", "X")
    temperature = (args.temperature if args.temperature is not None else get_config_value(config, "llm","temperature", 0.1))
    max_tokens = (args.max_tokens if args.max_tokens is not None else get_config_value(config, "llm", "max_tokens", 192))
    log_level = get_config_value(config, "logging", "level", "INFO")
    log_file = get_config_value(config, "logging", "log_file", None)

    if not index_dir:
        raise ValueError("index_dir must be provided by --index_dir or config file")

    logger = setup_logger("research_agent", level=log_level, log_file=log_file)
    logger.info("Agent started")
    logger.info(f"query={args.query}")
    logger.info(
        "config: "
        f"index_dir={index_dir}, "
        f"eval_file={eval_file}, "
        f"retriever={retriever}, "
        f"top_k={top_k}, "
        f"alpha={alpha}, "
        f"rerank={rerank}, "
        f"candidate_k={candidate_k}, "
        f"llm={llm}, "
        f"model_name={model_name}"
    )

    agent = ResearchAgent(
        index_dir=index_dir,
        eval_file=eval_file,
        retriever=retriever,
        top_k=top_k,
        alpha=alpha,
        rerank=rerank,
        candidate_k=candidate_k,
        llm=llm,
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        logger=logger,
    )

    result = agent.run(args.query)
    logger.info(f"intent={result['type']}")
    print_agent_result(result)
    logger.info("Agent finished")


if __name__ == "__main__":
    main()