from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str):
        if not model_name:
            raise ValueError("model_name must not be empty")

        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self,query: str,candidates: list[dict],top_k: int = 5,) -> list[dict]:
        
        if not query:
            raise ValueError("query must not be empty")
        if not isinstance(candidates, list):
            raise TypeError("candidates must be a list of dictionaries")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        if not candidates:
            return []
        
        pairs = []
        for candidate in candidates:
            if "text" not in candidate:
                raise ValueError("each candidate must contain a text field")
            pairs.append((query, candidate["text"]))
        scores = self.model.predict(pairs)

        reranked = []
        for candidate, score in zip(candidates, scores):
            item = candidate.copy()
            item["rerank_score"] = float(score)
            reranked.append(item)
        reranked.sort(key=lambda item: item["rerank_score"], reverse=True)

        return reranked[:top_k]
