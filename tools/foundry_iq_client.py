from config.settings import Settings


class FoundryIQClient:
    """
    Client for Foundry IQ — grounded knowledge retrieval for AI agents.
    Connects to Azure AI Foundry to query Azure Architecture Center,
    Cloud Adoption Framework, and Well-Architected Framework knowledge.
    In DEMO_MODE, returns structured mock responses.
    """

    def __init__(self):
        self.demo_mode = Settings.DEMO_MODE
        if not self.demo_mode:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                azure_endpoint=Settings.AZURE_OPENAI_ENDPOINT,
                api_key=Settings.AZURE_OPENAI_API_KEY,
                api_version="2024-05-01-preview",
            )

    def query(self, prompt: str, domain: str = "general") -> str:
        """
        Query Foundry IQ with a grounded prompt.
        In live mode, calls Azure OpenAI with RAG over Azure docs.
        In demo mode, returns placeholder response.
        """
        if self.demo_mode:
            return '[]'

        system_prompt = (
            "You are an Azure architecture expert grounded in Microsoft Azure Architecture Center, "
            "Cloud Adoption Framework, and Well-Architected Framework documentation. "
            "Always cite official Microsoft reference URLs in your responses. "
            "Be precise, actionable, and enterprise-grade."
        )

        response = self.client.chat.completions.create(
            model=Settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
