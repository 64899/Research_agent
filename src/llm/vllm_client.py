class MockLLMClient:
    def generate(self,prompt: str,temperature: float = 0.2,max_tokens: int = 1024,) -> str:
        if not prompt:
            raise ValueError("prompt must not be empty")

        return (
            "This is a mock answer. "
            "LLM generation is not connected yet, but retrieval and prompt construction are working."
        )