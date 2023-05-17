from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import poe

class QuoraPOE(LLMSource):
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        super(QuoraPOE, self).__init__(client, config, db)
        self.poe_client = poe.Client(self.config.poe_auth_cookie)

    def on_config_reloaded(self):
        self.poe_client = poe.Client(self.config.poe_auth_cookie)

    def on_purge(self):
        logger.debug("Sending chat break")
        self.poe_client.send_chat_break(self.config.poe_model)

    def on_message_delete(self, message: discord.Message):
        pass

    @property
    def current_model_name(self) -> str:
        return self.config.poe_model

    def set_model(self, model_id: str) -> None:
        self.config.poe_model = model_id

    async def list_models(self) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=name, value=codename, default=self.config.poe_model == codename) for codename, name in self.poe_client.bot_names.items()]

    async def generate_response(self, invoker: discord.User = None) -> str:
        # get last message
        author_id, content, mid = self.db.get_recent_messages(1)[0]

        message = content + "\n\n"
        message += self.get_initial(invoker)
        if self.config.bot_reminder:
            message += "\n\nReminder: " + self.config.bot_reminder

        for chunk in self.poe_client.send_message(self.config.poe_model, message):
            print(chunk['text'])
        return chunk['text']

