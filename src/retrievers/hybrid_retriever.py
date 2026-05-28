
def normalize_scores(results: list[dict]) -> dict[str, float]:
    if not results:
        return {}

    scores = [result["score"] for result in results]
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return {result["chunk_id"]: 1.0 for result in results}

    normalized = {}
    for result in results:
        normalized[result["chunk_id"]] = (
            (result["score"] - min_score) / (max_score - min_score)
        )

    return normalized


class HybridRetriever:
    def __init__(self, dense_retriever, bm25_retriever, alpha: float = 0.5):
        if alpha < 0 or alpha > 1:
            raise ValueError("alpha must be between 0 and 1")

        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.alpha = alpha

    def search(self, query: str, top_k: int = 5) -> list[dict]:

        if not query:
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        
        candidate_k = top_k * 3

        dense_results = self.dense_retriever.search(query, top_k=candidate_k)
        bm25_results = self.bm25_retriever.search(query, top_k=candidate_k)

        dense_scores = normalize_scores(dense_results)
        bm25_scores = normalize_scores(bm25_results)

        candidates = {}
        
        for result in dense_results:
            candidates[result["chunk_id"]] = result.copy()

        for result in bm25_results:
            candidates[result["chunk_id"]] = result.copy()

        fused_results = []
        for chunk_id, candidate in candidates.items():
            dense_score = dense_scores.get(chunk_id, 0.0)
            bm25_score = bm25_scores.get(chunk_id, 0.0)

            final_score = self.alpha * dense_score + (1 - self.alpha) * bm25_score

            candidate["dense_score"] = dense_score
            candidate["bm25_score"] = bm25_score
            candidate["score"] = final_score

            fused_results.append(candidate)

        fused_results.sort(key=lambda item: item["score"], reverse=True)

        return fused_results[:top_k]