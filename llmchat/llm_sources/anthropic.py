from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import anthropic

class Anthropic(LLMSource):
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        super(Anthropic, self).__init__(client, config, db)
        self.anthropic_client = anthropic.Client(self.config.anthropic_key)
    def on_config_reloaded(self):
        self.anthropic_client = anthropic.Client(self.config.anthropic_key)

    def on_purge(self):
        pass

    def on_message_delete(self, message: discord.Message):
        pass

    def set_model(self, model_id: str) -> None:
        self.config.anthropic_model = model_id

    @property
    def current_model_name(self) -> str:
        return self.config.anthropic_model
    async def list_models(self) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=v, value=v, default=False) for v in [
            'claude-v1', 'claude-v1-100k', 'claude-instant-v1', 'claude-instant-v1-100k', 'claude-v1.3', 'claude-v1.3-100k', 'claude-v1.2', 'claude-v1.0',
            'claude-instant-v1.1', 'claude-instant-v1.1-100k', 'claude-instant-v1.0']]

    async def generate_response(self, invoker: discord.User = None) -> str:
        context = f"{anthropic.HUMAN_PROMPT} {self.get_initial(invoker).strip()}"
        reminder = f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n" if self.config.bot_reminder else ""
        end = reminder + anthropic.AI_PROMPT

        fmt_message = ""
        for m in self.db.get_recent_messages(self.config.llm_context_messages_count):
            author_id, content, message_id = m
            if author_id == -1:
                continue
            elif author_id == self.client.user.id:
                fmt_message += f"{anthropic.AI_PROMPT} {content}"
            else:
                fmt_message += f"{anthropic.HUMAN_PROMPT} {content}"

        context += fmt_message
        context += end
        logger.debug(f"Context: {context}")

        return (await self.anthropic_client.acompletion(
            prompt=context,
            model=self.config.anthropic_model,
            stop_sequences=[anthropic.HUMAN_PROMPT],
            temperature=self.config.llm_temperature,
            max_tokens_to_sample=self.config.llm_max_tokens or 99999
        ))["completion"]

