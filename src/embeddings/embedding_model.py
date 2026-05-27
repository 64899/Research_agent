from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    def __init__(self, model_name: str):
        if not model_name:
            raise ValueError("model_name must not be empty")
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")

        for text in texts:

            if not isinstance(text, str):
                raise TypeError("each item in texts must be a string")
            if not texts:
                return []
             
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
        