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
        self.update_encoding()
        self.on_config_reloaded()

    async def check_model(self):
        assert (
            self.config.openai_model in self.list_models()
        ), f"Failed to find OpenAI model!"
        if self.use_chat_completion:
            logger.warn(
                f"Chat completion model is selected! ({self.config.openai_model}) This might yield different results than using a text completion model like davinci."
            )

    def on_config_reloaded(self):
        openai.api_key = self.config.openai_key

    async def list_models(self) -> list[discord.SelectOption]:
        async with ClientSession() as c:
            openai.aiosession.set(c)
            # fix api requestor error
            all_models = openai.Model.list(api_base=self.config.openai_reverse_proxy_url)
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
                logger.debug(f"Failed to get encoder for OpenAI model: {self.config.openai_model}. Using default (cl100k_base)")
                self.encoding = tiktoken.get_encoding("cl100k_base")

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
        async with ClientSession() as s:
            openai.aiosession.set(s)

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
                        api_base=self.config.openai_reverse_proxy_url,
                        model=self.config.openai_model,
                        prompt=prompt,
                        stop="\n",
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
                        api_base=self.config.openai_reverse_proxy_url,
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

                if not response:
                    raise Exception("Response from OpenAI API was empty!")
                return response
            except openai.error.APIConnectionError as e:
                # https://github.com/openai/openai-python/issues/371
                if _retry_count == 3:
                    raise e
                logger.warn(f"Connection reset error, Retrying ({_retry_count})...")
                return await self.generate_response(_retry_count=_retry_count + 1)

    async def get_context_gpt3(self, invoker: discord.User = None) -> str:
        self.update_encoding()
        context = self.get_initial(invoker).strip() + "\n"
        reminder = f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}\n" if self.config.bot_reminder else ""
        end = reminder + f"{self.config.bot_name}: "

        min_token_count = self.get_token_count(context + end)
        cur_token_count = min_token_count

        if cur_token_count > GPT_3_MAX_TOKENS:
            raise Exception(f"Please shorten your reminder / initial prompt. Max token count exceeded: {cur_token_count} > {GPT_3_MAX_TOKENS}")

        all_messages = self.db.get_recent_messages()
        recent_messages = all_messages[-self.config.llm_context_messages_count:]
        ooc_messages = all_messages[:-self.config.llm_context_messages_count]  # everything but the messages in the context limit

        similar_messages = []
        if self.config.openai_use_embeddings and ooc_messages:
            similar_matches = self.similar_messages(recent_messages[-1], ooc_messages)
            if similar_matches:
                logger.debug("Bot will be reminded of:\n\t" + '\n\t'.join([f"{message[1]} ({round(similarity * 100)}% similar)" for message, similarity in similar_matches]))
                # sort by message_id
                messages, similarities = list(zip(*similar_matches))
                similar_messages = list(messages)
                similar_messages.sort(key=lambda m: m[2])

        for i in similar_messages+recent_messages:
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
            fmt_message += "\n"
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

    def similar_messages(self, last_message, messages_pool):
        similar_matches = []
        similarity_threshold = self.config.openai_similarity_threshold  # messages with a similarity rating equal to or above this number will be included in the reminder.
        # get embedding for last message
        last_message_embedding = self.db.query_embedding(last_message[2])
        if last_message_embedding:
            similar_matches = self.db.get_most_similar(last_message_embedding, threshold=similarity_threshold, messages_pool=messages_pool)[:self.config.openai_max_similar_messages]
        else:
            logger.warn("Unable to find embedding for message " + last_message[2])
        return similar_matches

    def get_context_gpt4(self, invoker: discord.User = None) -> list[dict]:
        self.update_encoding()
        initial = self.get_initial(invoker)
        reminder = f"Reminder: {self._insert_wildcards(self.config.bot_reminder, self.db.get_identity(invoker.id))}" if self.config.bot_reminder else ""

        min_token_count = self.get_token_count(initial) + 4 + (self.get_token_count(reminder) + 4 if reminder else 0)
        max_token_count = GPT_4_MAX_TOKENS if "32k" not in self.config.openai_model else GPT_4_32K_MAX_TOKENS
        cur_token_count = min_token_count

        if cur_token_count > max_token_count:
            raise Exception(f"Please shorten your reminder / initial prompt. Max token count exceeded: {cur_token_count} > {max_token_count}")

        ret = []

        def format_message(message):
            author_id, content, mid = message
            role = "user"
            if author_id == -1:
                role = "system"
            elif author_id == self.client.user.id:
                role = "assistant"

            return {"role": role, "content": content}

        all_messages = self.db.get_recent_messages()
        recent_messages = all_messages[-self.config.llm_context_messages_count:]
        ooc_messages = all_messages[:-self.config.llm_context_messages_count]  # everything but the messages in the context limit

        similar_messages = []
        if self.config.openai_use_embeddings and ooc_messages:
            similar_matches = self.similar_messages(recent_messages[-1], ooc_messages)
            if similar_matches:
                logger.debug("Bot will be reminded of:\n\t"+'\n\t'.join([f"{message[1]} ({round(similarity * 100)}% similar)" for message, similarity in similar_matches]))
                # sort by message_id
                messages, similarities = list(zip(*similar_matches))
                similar_messages = list(messages)
                similar_messages.sort(key=lambda m: m[2])

        ret.append({"role": "system", "content": initial})

        fmt_messages = list(map(format_message, similar_messages+recent_messages))

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
