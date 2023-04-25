from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import openai
import asyncio
from aiohttp import ClientSession

class OpenAI(LLMSource):
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        super(OpenAI, self).__init__(client, config, db)
        openai.api_key = config.openai_key

    async def check_model(self):
        assert (
            self.config.openai_model in self.list_models()
        ), f"Failed to find OpenAI model!"
        if self.use_chat_completion:
            logger.warn(
                f"Chat completion model is selected! ({self.config.openai_model}) This might yield different results than using a text completion model like davinci."
            )

    def list_models(self) -> list[str]:
        all_models = openai.Model.list()
        ret = [
            m.id
            for m in all_models.data
            if (m.id.startswith("gpt") or m.id.startswith("text-"))
            and not ("-search-" in m.id or "-similarity-" in m.id)
        ]
        ret.sort()
        return ret

    def set_model(self, model_id: str) -> None:
        logger.info(f"OpenAI model set to {model_id}")
        self.config.openai_model = model_id

    @property
    def is_openai(self) -> bool:
        return True

    @property
    def use_chat_completion(self):
        return self.config.openai_model.startswith(
            "gpt-4"
        ) or self.config.openai_model.startswith("gpt-3.5")

    async def generate_response(
        self, invoker: discord.User = None, _retry_count=0
    ) -> str:
        openai.aiosession.set(ClientSession())
        try:
            if not self.use_chat_completion:
                response = await openai.Completion.acreate(
                    model=self.config.openai_model,
                    prompt=await self.get_context_gpt3(invoker),
                    stop="\n$$$",
                    max_tokens=400
                    if self.config.llm_max_tokens == 0
                    else self.config.llm_max_tokens,
                    temperature=self.config.llm_temperature,
                    presence_penalty=self.config.llm_presence_penalty,
                    frequency_penalty=self.config.llm_frequency_penalty,
                )
                logger.debug(f"{response.usage.total_tokens} tokens used")
                response = response.choices[0].text.strip()
            else:
                response = await openai.ChatCompletion.acreate(
                    model=self.config.openai_model,
                    max_tokens=None
                    if self.config.llm_max_tokens == 0
                    else self.config.llm_max_tokens,
                    messages=self.get_context_gpt4(invoker),
                    temperature=self.config.llm_temperature,
                    presence_penalty=self.config.llm_presence_penalty,
                    frequency_penalty=self.config.llm_frequency_penalty,
                )
                logger.debug(f"{response.usage.total_tokens} tokens used")
                response = response.choices[0].message.content.strip()
            await openai.aiosession.get().close()
            return response
        except openai.error.APIConnectionError as e:
            # https://github.com/openai/openai-python/issues/371
            if _retry_count == 3:
                raise e
            logger.warn(f"Connection reset error, Retrying ({_retry_count})...")
            return await self.generate_response(_retry_count=_retry_count + 1)

    async def get_context_gpt3(self, invoker: discord.User = None) -> str:
        context = self.get_initial(invoker).strip() + " Each message is separated by a new line followed by '$$$'.\n"

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
            context += "\n$$$\n"

        if self.config.bot_reminder:
            context += f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n"

        context += f"{self.config.bot_name}: "
        logger.debug(f"Context: {context}")
        return context

    def get_context_gpt4(self, invoker: discord.User = None) -> list[object]:
        initial = self.get_initial(invoker)

        def format_message(message):
            author_id, content, mid = message
            role = "user"
            if author_id == -1:
                role = "system"
            elif author_id == self.client.user.id:
                role = "assistant"

            return {"role": role, "content": content}

        ret = list(
            map(
                format_message,
                self.db.get_recent_messages(self.config.llm_context_messages_count),
            )
        )
        ret.insert(0, {"role": "system", "content": initial})

        if self.config.bot_reminder:
            ret.append({"role": "system", "content": f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}"})

        logger.debug(str(ret))
        return ret

    @property
    def current_model_name(self) -> str:
        return self.config.openai_model
