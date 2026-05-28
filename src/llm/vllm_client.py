from openai import OpenAI

class MockLLMClient:
    def generate(self,prompt: str,temperature: float = 0.2,max_tokens: int = 1024,) -> str:
        if not prompt:
            raise ValueError("prompt must not be empty")

        return (
            "This is a mock answer. "
            "LLM generation is not connected yet, but retrieval and prompt construction are working."
        )
    

class VLLMClient:
    def __init__(self, base_url: str, api_key: str, model_name: str):
        
        if not base_url:
            raise ValueError("base_url must not be empty")
        if not api_key:
            raise ValueError("api_key must not be empty")
        if not model_name:
            raise ValueError("model_name must not be empty")

        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.client = OpenAI(base_url=base_url,api_key=api_key,)
        
    def generate(self,prompt: str,temperature: float = 0.2,max_tokens: int = 1024,) -> str:
        
        if not prompt:
            raise ValueError("prompt must not be empty")

        response = self.client.chat.completions.create(model=self.model_name,
            messages=[
                {
                        "role": "user",
                        "content": prompt,
                }
                    ],
        temperature=temperature,max_tokens=max_tokens,)

        return response.choices[0].message.content or ""