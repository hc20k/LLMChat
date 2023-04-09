from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData

class LLMSource:
    def __init__(self, client: Client, config: Config, db: PersistentData):
        self.config = config
        self.db = db
        self.client = client

    async def generate_response(self, invoker: User = None) -> str:
        return NotImplementedError()

    async def list_models(self) -> list[str]:
        return NotImplementedError()

    def set_model(self, model_id: str) -> None:
        return NotImplementedError()

    @property
    def is_openai(self) -> bool:
        return False

    @property
    def current_model_name(self) -> str:
        return "Unknown LLM"
