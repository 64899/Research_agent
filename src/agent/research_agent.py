import logging
from src.tools.evaluation_tool import evaluate_retrieval_tool
from src.tools.rag_tool import answer_question
from src.tools.retrieval_tool import retrieve_chunks

class ResearchAgent:
    def __init__(
        self,
        index_dir: str,
        eval_file: str | None = None,
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
        logger: logging.Logger | None = None,
    ):
        if not index_dir:
            raise ValueError("index_dir must not be empty")

        self.index_dir = index_dir
        self.eval_file = eval_file
        self.retriever = retriever
        self.top_k = top_k
        self.alpha = alpha
        self.rerank = rerank
        self.candidate_k = candidate_k
        self.llm = llm
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = logger or logging.getLogger(__name__)

        
    def detect_intent(self, user_input: str) -> str:
        text = user_input.lower()

        retrieve_keywords = ["retrieve", "search", "find chunks", "show chunks"]
        evaluate_keywords = ["evaluate", "evaluation", "metric", "mrr", "recall", "hit"]

        for keyword in evaluate_keywords:
            if keyword in text:
                return "evaluate"

        for keyword in retrieve_keywords:
            if keyword in text:
                return "retrieve"

        return "answer"


    def run(self, user_input: str) -> dict:
        if not user_input:
            raise ValueError("user_input must not be empty")

        intent = self.detect_intent(user_input)
        self.logger.info(f"detected_intent={intent}")

        if intent == "answer":
            self.logger.info("calling_tool=answer_question")
            result = answer_question(
                index_dir=self.index_dir,
                query=user_input,
                retriever=self.retriever,
                top_k=self.top_k,
                alpha=self.alpha,
                rerank=self.rerank,
                candidate_k=self.candidate_k,
                llm=self.llm,
                base_url=self.base_url,
                api_key=self.api_key,
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                logger=self.logger,
            )
            return {
                "type": "answer",
                "input": user_input,
                "result": result,
            }
        

        if intent == "retrieve":
            self.logger.info("calling_tool=retrieve_chunks")
            chunks = retrieve_chunks(
                index_dir=self.index_dir,
                query=user_input,
                retriever=self.retriever,
                top_k=self.top_k,
                alpha=self.alpha,
                rerank=self.rerank,
                candidate_k=self.candidate_k,
                logger=self.logger,
            )
            return {
                "type": "retrieve",
                "input": user_input,
                "chunks": chunks,
            }
        

        if intent == "evaluate":
            if not self.eval_file:
                raise ValueError("eval_file is required for evaluation")

            self.logger.info("calling_tool=evaluate_retrieval_tool")
            result = evaluate_retrieval_tool(
                index_dir=self.index_dir,
                eval_file=self.eval_file,
                retriever=self.retriever,
                top_k=self.top_k,
                alpha=self.alpha,
                rerank=self.rerank,
                candidate_k=self.candidate_k,
                logger=self.logger,
            )

            return {
                "type": "evaluate",
                "input": user_input,
                "result": result,
            }
        

        return {
            "type": intent,
            "input": user_input,
            "message": "Agent routing detected.",
        }
    
def print_agent_result(result: dict) -> None:
    print(f"Type: {result['type']}")
    print(f"Input: {result['input']}")
    print()

    if result["type"] == "answer":
        answer_result = result["result"]

        print("Answer:")
        print(answer_result["answer"])
        print()

        print("Sources:")
        for i, source in enumerate(answer_result["sources"], start=1):
            print(
                f"[{i}] {source['source']}, "
                f"page {source['page']}, "
                f"chunk_id={source['chunk_id']}"
            )

    elif result["type"] == "retrieve":
        print("Chunks:")
        for i, chunk in enumerate(result["chunks"], start=1):
            print(
                f"[{i}] {chunk['source']}, "
                f"page {chunk['page']}, "
                f"chunk_id={chunk['chunk_id']}"
            )
            print(chunk["text"][:300])
            print("-" * 80)

    elif result["type"] == "evaluate":
        overall = result["result"]["overall"]

        print("Overall:")
        print(f"Mean Hit: {overall['mean_hit']:.4f}")
        print(f"Mean Recall: {overall['mean_recall']:.4f}")
        print(f"Mean MRR: {overall['mean_mrr']:.4f}")

    else:
        print(result.get("message", "No message."))
