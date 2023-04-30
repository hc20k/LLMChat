from . import LLMSource
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import discord
import openai
from aiohttp import ClientSession
import tiktoken
from typing import Union

GPT_3_MAX_TOKENS = 2048
GPT_4_MAX_TOKENS = 8192
GPT_4_32K_MAX_TOKENS = 32768

class OpenAI(LLMSource):
    encoding: tiktoken.Encoding = None
    def __init__(self, client: discord.Client, config: Config, db: PersistentData):
        super(OpenAI, self).__init__(client, config, db)
        openai.api_key = config.openai_key
        self.update_encoding()

    async def check_model(self):
        assert (
            self.config.openai_model in self.list_models()
        ), f"Failed to find OpenAI model!"
        if self.use_chat_completion:
            logger.warn(
                f"Chat completion model is selected! ({self.config.openai_model}) This might yield different results than using a text completion model like davinci."
            )

    def list_models(self) -> list[discord.SelectOption]:
        all_models = openai.Model.list()
        ret = [
            m.id
            for m in all_models.data
            if not ("-search-" in m.id or "-similarity-" in m.id)
        ]
        ret.sort()
        return [discord.SelectOption(label=m, value=m, default=self.config.openai_model == m) for m in ret]

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

    def update_encoding(self):
        encoder_name = self.config.openai_model

        if not self.encoding or self.encoding.name != encoder_name:
            logger.debug(f"Updating tokenizer encoding for {self.config.openai_model}")
            try:
                self.encoding = tiktoken.encoding_for_model(encoder_name)
            except KeyError as e:
                logger.debug(f"Failed to get encoder for OpenAI model: {self.config.openai_model} {str(e)}")
                return -1

    def get_token_count(self, content: Union[str, list[dict], dict]) -> int:
        if isinstance(content, str):
            # <= gpt3
            content: str = content
            return len(self.encoding.encode(content))
        elif isinstance(content, dict):
            return self.get_token_count(content["content"]) + self.get_token_count(content["role"]) + 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        elif isinstance(content, list):
            # >= gpt3.5
            content: list[dict] = content
            count = 0
            for entry in content:
                count += self.get_token_count(entry)
            return count
        else:
            # wtf
            raise Exception(f"Can't get token count of unhandled type {type(content).__name__}")



    async def generate_response(
        self, invoker: discord.User = None, _retry_count=0
    ) -> str:
        openai.aiosession.set(ClientSession())
        try:
            if not self.use_chat_completion:
                completion_tokens = 400 if self.config.llm_max_tokens == 0 else self.config.llm_max_tokens
                prompt = await self.get_context_gpt3(invoker)
                token_count = self.get_token_count(prompt)

                if token_count + completion_tokens > GPT_3_MAX_TOKENS:
                    completion_tokens = GPT_3_MAX_TOKENS - token_count
                    if completion_tokens < 0:
                        raise Exception(f"Token limit exceeded! ({token_count} > {GPT_3_MAX_TOKENS}) Please make your initial context shorter or reduce the message context count!")

                response = await openai.Completion.acreate(
                    model=self.config.openai_model,
                    prompt=prompt,
                    stop="\n$$$",
                    max_tokens=completion_tokens,
                    temperature=self.config.llm_temperature,
                    presence_penalty=self.config.llm_presence_penalty,
                    frequency_penalty=self.config.llm_frequency_penalty,
                )
                logger.debug(f"{response.usage.total_tokens} tokens used")
                response = response.choices[0].text.strip()
            else:
                completion_tokens = self.config.llm_max_tokens
                messages = self.get_context_gpt4(invoker)
                token_count = self.get_token_count(messages)
                model_max_tokens = GPT_4_MAX_TOKENS if "32k" not in self.config.openai_model else GPT_4_32K_MAX_TOKENS

                if token_count + completion_tokens > model_max_tokens:
                    completion_tokens = model_max_tokens - token_count
                    if completion_tokens < 0:
                        raise Exception(f"Token limit exceeded! ({token_count} > {model_max_tokens}) Please make your initial context shorter or reduce the message context count!")

                response = await openai.ChatCompletion.acreate(
                    model=self.config.openai_model,
                    max_tokens=None
                    if completion_tokens == 0
                    else completion_tokens,
                    messages=messages,
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
        self.update_encoding()
        context = self.get_initial(invoker).strip() + " Each message is separated by a new line followed by '$$$'.\n"
        reminder = f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n" if self.config.bot_reminder else ""
        end = reminder + f"{self.config.bot_name}: "

        min_token_count = self.get_token_count(context + end)
        cur_token_count = min_token_count

        if cur_token_count > GPT_3_MAX_TOKENS:
            raise Exception(f"Please shorten your reminder / initial prompt. Max token count exceeded: {cur_token_count} > {GPT_3_MAX_TOKENS}")

        for i in self.db.get_recent_messages(self.config.llm_context_messages_count):
            fmt_message = ""
            author_id, content, message_id = i
            if author_id == -1:
                continue
            elif author_id == self.client.user.id:
                fmt_message += f"{self.config.bot_name}: {content}"
            else:
                name = (await self.client.fetch_user(author_id)).display_name
                identity = self.db.get_identity(author_id)
                if identity is not None:
                    name_, identity = identity
                    name = name_

                fmt_message += f"{name}: {content}"
            fmt_message += "\n$$$\n"
            token_count = self.get_token_count(fmt_message)
            if cur_token_count + token_count > GPT_3_MAX_TOKENS:
                logger.warn(f"Maximum token count reached ({cur_token_count} + {token_count} > {GPT_3_MAX_TOKENS}). Context will be shorter than expected.")
                break
            else:
                context += fmt_message
                cur_token_count += token_count

        context += end
        logger.debug(f"Calculated prompt token count: {cur_token_count}")
        logger.debug(f"Context: {context}")
        return context

    def get_context_gpt4(self, invoker: discord.User = None) -> list[dict]:
        self.update_encoding()
        initial = self.get_initial(invoker)
        reminder = f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}" if self.config.bot_reminder else ""

        min_token_count = self.get_token_count(initial) + 4 + (self.get_token_count(reminder) + 4 if reminder else 0)
        max_token_count = GPT_4_MAX_TOKENS if "32k" not in self.config.openai_model else GPT_4_32K_MAX_TOKENS
        cur_token_count = min_token_count

        if cur_token_count > max_token_count:
            raise Exception(f"Please shorten your reminder / initial prompt. Max token count exceeded: {cur_token_count} > {max_token_count}")

        def format_message(message):
            author_id, content, mid = message
            role = "user"
            if author_id == -1:
                role = "system"
            elif author_id == self.client.user.id:
                role = "assistant"

            return {"role": role, "content": content}

        fmt_messages = list(map(format_message, self.db.get_recent_messages(self.config.llm_context_messages_count)))

        ret = [{"role": "system", "content": initial}]
        for m in fmt_messages:
            token_count = self.get_token_count(m)
            if cur_token_count + token_count > max_token_count:
                logger.warn(f"Maximum token count reached ({cur_token_count} + {token_count} > {max_token_count}). Context will be shorter than expected.")
                break
            else:
                ret.append(m)
                cur_token_count += token_count

        if reminder:
            ret.append({"role": "system", "content": reminder})

        cur_token_count += 2

        logger.debug(f"Calculated prompt token count: {cur_token_count}")
        logger.debug(str(ret))
        return ret

    @property
    def current_model_name(self) -> str:
        return self.config.openai_model
