from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import os
from langchain.llms import LlamaCpp
import functools
import time

class LLaMA(LLMSource):
    model: LlamaCpp = None
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        super(LLaMA, self).__init__(client, config, db)
        self.load_model()

    def load_model(self):
        if len(self.config.llama_model_name) == 0:
            logger.warn(
                "No LLaMA model specified: 'LLaMA.model_name' is blank. Choose a model with /model"
            )
            return

        model_path = os.path.join(
            self.config.llama_search_path, self.config.llama_model_name
        )
        if not os.path.exists(model_path):
            logger.warn("LLaMA model", model_path, "doesn't exist!")
            return

        self.model = LlamaCpp(
            model_path=model_path,
            n_ctx=2048,
            max_tokens=self.config.llm_max_tokens or 256,
            temperature=self.config.llm_temperature,
            repeat_penalty=self.config.llm_frequency_penalty,  # ~1.1 is a good value
        )
        # f16_kv is half precision, n_ctx is context window

    async def list_models(self) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=f, value=f, default=self.config.llama_model_name == f) for f in os.listdir(self.config.llama_search_path)]

    def set_model(self, model_id: str) -> None:
        self.config.llama_model_name = model_id
        self.load_model()

    async def get_context(self, invoker: discord.User = None):
        context = self.get_initial(invoker).strip() + "\n"

        for i in self.db.get_recent_messages(self.config.llm_context_messages_count):
            author_id, content, message_id = i
            if author_id == -1:
                continue
            elif author_id == self.client.user.id:
                context += f"{self.config.bot_name}: {content}"
            else:
                name = (await self.client.fetch_user(author_id)).display_name
                identity = self.db.get_identity(author_id)
                if identity is not None:
                    name_, identity = identity
                    name = name_

                context += f"{name}: {content}"
            context += "\n"

        if self.config.bot_reminder:
            context += f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n"

        context += f"{self.config.bot_name}: "
        return context

    def _generate(self, context: str) -> str:
        ret = ""
        start_time = time.time()
        for chunk in self.model.stream(context, stop=["\n"]):
            ret += chunk["choices"][0]["text"]
            logger.debug(ret)

        logger.debug(f"Generation took {time.time() - start_time}s")
        if not len(ret):
            raise Exception("LLM generated an empty message!")
        return ret

    async def generate_response(self, invoker: discord.User = None) -> str:
        if self.model is None:
            raise Exception("Model not yet loaded! Use /model to load one.")

        context = await self.get_context(invoker)
        logger.debug(context)

        blocking = functools.partial(self._generate, context)
        return await self.client.loop.run_in_executor(None, blocking)


    @property
    def current_model_name(self) -> str:
        if len(self.config.llama_model_name) == 0:
            return "*Not loaded!*"
        return self.config.llama_model_name
