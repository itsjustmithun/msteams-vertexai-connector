class VertexAIProvider:
    def __init__(self, model_name: str, project: str, location: str) -> None:
        if not model_name or not project or not location:
            raise ValueError("Missing Vertex AI configuration.")

        self.model_name = model_name
        from langchain_google_genai import ChatGoogleGenerativeAI

        self._client = ChatGoogleGenerativeAI(
            model=model_name,
            project=project,
            location=location,
            vertexai=True,
            temperature=0.2,
        )

    def generate(self, prompt: str) -> str:
        response = self._client.invoke(prompt)
        if hasattr(response, "text"):
            return response.text
        if hasattr(response, "content"):
            return response.content
        return str(response)
