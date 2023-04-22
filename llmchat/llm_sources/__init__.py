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

    def list_models(self) -> list[str]:
        return NotImplementedError()

    def set_model(self, model_id: str) -> None:
        return NotImplementedError()

    def get_initial(self, invoker: User = None) -> str:
        user_identity = ("User", None)
        if invoker:
            fetched_identity = self.db.get_identity(invoker.id)
            if not fetched_identity:
                user_identity = (invoker.display_name, f"{invoker.display_name} is a human that has not set their identity. Remind them to set it using /your_identity!")
            else:
                user_identity = fetched_identity

        user_name, user_desc = user_identity
        return self.config.bot_initial_prompt.replace("{bot_name}", self.config.bot_name).replace("{bot_identity}", self.config.bot_identity).replace("{user_name}", user_name).replace("{user_identity}", user_desc)

    @property
    def is_openai(self) -> bool:
        return False

    @property
    def current_model_name(self) -> str:
        return "Unknown LLM"
