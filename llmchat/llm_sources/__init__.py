from discord import User, Client, SelectOption
from llmchat.config import Config
from llmchat.persistence import PersistentData
from datetime import datetime

class LLMSource:
    def __init__(self, client: Client, config: Config, db: PersistentData):
        self.config = config
        self.db = db
        self.client = client

    async def generate_response(self, invoker: User = None) -> str:
        return NotImplementedError()

    async def list_models(self) -> list[SelectOption]:
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

        return self._insert_wildcards(self.config.bot_initial_prompt, user_identity)

    def _insert_wildcards(self, text: str, user_info: tuple = None) -> str:
        user_name, user_identity = user_info or (None, None)
        wildcards = {
            "bot_name": self.config.bot_name,
            "bot_identity": self.config.bot_identity,
            "user_name": user_name,
            "user_identity": user_identity,
            "date": datetime.now().strftime("%A, %B %d, %Y %H:%M"),
            "nl": "\n",
        }

        for wc, value in wildcards.items():
            if value:
                text = text.replace("{" + wc + "}", value)

        return text

    @property
    def is_openai(self) -> bool:
        return False

    @property
    def current_model_name(self) -> str:
        return "Unknown LLM"

    def on_config_reloaded(self):
        pass