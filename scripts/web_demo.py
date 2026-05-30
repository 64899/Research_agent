#python -m scripts.web_demo
import shutil
from pathlib import Path

import gradio as gr

from src.agent.research_agent import ResearchAgent
from src.chunkers.fixed_chunker import chunk_documents
from src.config.config_loader import load_config
from src.embeddings.embedding_model import EmbeddingModel
from src.index.bm25_index import BM25Index
from src.index.vector_store import VectorStore
from src.loaders.pdf_loader import load_pdf
from src.utils.logger import setup_logger


WEBUI_INDEX_DIR = "data/index/webui_demo"


def get_config_value(config: dict, section: str, key: str, default=None):
    if not config:
        return default

    section_config = config.get(section, {})

    if not isinstance(section_config, dict):
        return default

    return section_config.get(key, default)


def build_webui_index(pdf_path: str) -> tuple[str, str]:
    pdf_path = pdf_path.strip()

    if not pdf_path:
        return WEBUI_INDEX_DIR, "Error: pdf_path is required."

    path = Path(pdf_path)

    if not path.exists():
        return WEBUI_INDEX_DIR, f"Error: PDF file not found: {pdf_path}"

    if not path.is_file():
        return WEBUI_INDEX_DIR, f"Error: PDF path is not a file: {pdf_path}"

    index_dir = Path(WEBUI_INDEX_DIR)
    data_index_dir = Path("data/index").resolve()
    resolved_index_dir = index_dir.resolve()

    if data_index_dir not in resolved_index_dir.parents and resolved_index_dir != data_index_dir:
        return WEBUI_INDEX_DIR, f"Error: unsafe index directory: {WEBUI_INDEX_DIR}"

    if index_dir.exists():
        shutil.rmtree(index_dir)

    documents = load_pdf(pdf_path)
    chunks = chunk_documents(documents, chunk_size=800, overlap=100)

    if not chunks:
        return WEBUI_INDEX_DIR, "Error: no chunks were created from this PDF."

    model = EmbeddingModel("sentence-transformers/all-MiniLM-L6-v2")

    vector_store = VectorStore(model)
    vector_store.build(chunks)
    vector_store.save(WEBUI_INDEX_DIR)

    bm25_index = BM25Index()
    bm25_index.build(chunks)
    bm25_index.save(WEBUI_INDEX_DIR)

    message = (
        "Built index successfully.\n"
        f"PDF: {pdf_path}\n"
        f"Documents: {len(documents)}\n"
        f"Chunks: {len(chunks)}\n"
        f"Index dir: {WEBUI_INDEX_DIR}\n"
        "Previous web UI index was overwritten."
    )

    return WEBUI_INDEX_DIR, message


def build_agent(config_path: str, index_dir_override: str) -> ResearchAgent:
    config = load_config(config_path)

    config_index_dir = get_config_value(config, "index", "index_dir")
    index_dir = index_dir_override.strip() if index_dir_override.strip() else config_index_dir

    eval_file = get_config_value(config, "index", "eval_file")
    retriever = get_config_value(config, "retrieval", "retriever", "bm25")
    top_k = get_config_value(config, "retrieval", "top_k", 3)
    alpha = get_config_value(config, "retrieval", "alpha", 0.3)

    rerank = get_config_value(config, "rerank", "enabled", False)
    candidate_k = get_config_value(config, "rerank", "candidate_k", 10)

    llm = get_config_value(config, "llm", "provider", "mock")
    base_url = get_config_value(config, "llm", "base_url", "http://localhost:7890/v1")
    api_key = get_config_value(config, "llm", "api_key", "abc123")
    model_name = get_config_value(config, "llm", "model_name", "X")
    temperature = get_config_value(config, "llm", "temperature", 0.1)
    max_tokens = get_config_value(config, "llm", "max_tokens", 192)

    log_level = get_config_value(config, "logging", "level", "INFO")
    log_file = get_config_value(config, "logging", "log_file", "logs/research_agent.log")

    if not index_dir:
        raise ValueError("index_dir must be provided by config file or UI input")

    logger = setup_logger("research_agent_web", level=log_level, log_file=log_file)

    return ResearchAgent(
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


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return "No sources."

    lines = []

    for i, source in enumerate(sources, start=1):
        score_parts = []

        if "score" in source:
            score_parts.append(f"score={source['score']:.4f}")
        if "dense_score" in source:
            score_parts.append(f"dense={source['dense_score']:.4f}")
        if "bm25_score" in source:
            score_parts.append(f"bm25={source['bm25_score']:.4f}")
        if "rerank_score" in source:
            score_parts.append(f"rerank={source['rerank_score']:.4f}")

        score_text = ""
        if score_parts:
            score_text = " | " + ", ".join(score_parts)

        lines.append(
            f"[{i}] {source['source']}, "
            f"page {source['page']}, "
            f"chunk_id={source['chunk_id']}"
            f"{score_text}"
        )

    return "\n".join(lines)


def format_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return "No chunks."

    lines = []

    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] {chunk['source']}, "
            f"page {chunk['page']}, "
            f"chunk_id={chunk['chunk_id']}"
        )
        lines.append(chunk["text"])
        lines.append("-" * 80)

    return "\n".join(lines)


def format_metrics(evaluation: dict) -> str:
    if not evaluation:
        return "No metrics."

    overall = evaluation.get("overall", {})

    lines = [
        "Overall:",
        f"Mean Hit: {overall.get('mean_hit', 0):.4f}",
        f"Mean Recall: {overall.get('mean_recall', 0):.4f}",
        f"Mean MRR: {overall.get('mean_mrr', 0):.4f}",
    ]

    return "\n".join(lines)


def format_agent_outputs(result: dict) -> tuple[str, str, str, str]:
    result_type = result.get("type")

    if result_type == "answer":
        rag_result = result.get("result", {})
        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])

        answer_text = f"Type: answer\n\n{answer}"
        sources_text = format_sources(sources)
        chunks_text = format_chunks(sources)
        metrics_text = "No metrics. This is answer mode."

        return answer_text, sources_text, chunks_text, metrics_text

    if result_type == "retrieve":
        chunks = result.get("chunks", [])

        answer_text = "Type: retrieve\n\nNo answer generated. This mode only retrieves chunks."
        sources_text = format_sources(chunks)
        chunks_text = format_chunks(chunks)
        metrics_text = "No metrics. This is retrieve mode."

        return answer_text, sources_text, chunks_text, metrics_text

    if result_type == "evaluate":
        evaluation = result.get("evaluation", {})

        answer_text = "Type: evaluate\n\nNo answer generated. This mode evaluates retrieval quality."
        sources_text = "No sources. This is evaluation mode."
        chunks_text = "No chunks. This is evaluation mode."
        metrics_text = format_metrics(evaluation)

        return answer_text, sources_text, chunks_text, metrics_text

    return str(result), "No sources.", "No chunks.", "No metrics."


def run_agent_web(config_path: str, index_dir: str, query: str) -> tuple[str, str, str, str]:
    if not config_path.strip():
        return "Error: config_path is required.", "", "", ""

    if not query.strip():
        return "Error: query is required.", "", "", ""

    try:
        agent = build_agent(config_path=config_path, index_dir_override=index_dir)
        result = agent.run(query.strip())
        return format_agent_outputs(result)
    except Exception as exc:
        return f"Error: {exc}", "", "", ""


def main() -> None:
    with gr.Blocks(title="ResearchAgent Demo") as demo:
        gr.Markdown("# ResearchAgent Demo")
        gr.Markdown("Minimal Web UI for ResearchAgent.")

        with gr.Row():
            config_path = gr.Textbox(
                label="Config path",
                value="configs/default.yaml",
                placeholder="configs/default.yaml",
            )
            index_dir = gr.Textbox(
                label="Index dir override",
                value="data/index/webui_demo",
                placeholder="data/index/webui_demo",
            )

        with gr.Row():
            pdf_path = gr.Textbox(
                label="PDF path",
                placeholder="data/raw/test.pdf",
            )
            build_button = gr.Button("Build Web UI Index")

        build_status = gr.Textbox(label="Build Status", lines=6)

        query = gr.Textbox(
            label="Query",
            value="What method does this paper propose?",
            lines=3,
        )

        run_button = gr.Button("Run Agent")

        with gr.Tabs():
            with gr.Tab("Answer"):
                answer_output = gr.Textbox(label="Answer", lines=12)

            with gr.Tab("Sources"):
                sources_output = gr.Textbox(label="Sources", lines=12)

            with gr.Tab("Chunks"):
                chunks_output = gr.Textbox(label="Chunks", lines=18)

            with gr.Tab("Metrics"):
                metrics_output = gr.Textbox(label="Metrics", lines=8)

        build_button.click(
            fn=build_webui_index,
            inputs=[pdf_path],
            outputs=[index_dir, build_status],
        )

        run_button.click(
            fn=run_agent_web,
            inputs=[config_path, index_dir, query],
            outputs=[answer_output, sources_output, chunks_output, metrics_output],
        )

    demo.launch()


if __name__ == "__main__":
    main()