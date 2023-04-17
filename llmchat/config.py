import configparser


class Config:
    def __init__(self, path="config.ini"):
        self.path = path
        self._config = configparser.ConfigParser(allow_no_value=True)
        self.load()

    def load(self):
        self._config.read(self.path)

    def save(self):
        with open(self.path, "w") as cf:
            self._config.write(cf)

    # all .ini fields

    @property
    def openai_key(self) -> str:
        return self._config.get("OpenAI", "key")

    @openai_key.setter
    def openai_key(self, key):
        self._config.set("OpenAI", "key", key)
        self.save()

    @property
    def openai_model(self) -> str:
        return self._config.get("OpenAI", "model")

    @openai_model.setter
    def openai_model(self, model_id):
        self._config.set("OpenAI", "model", model_id)
        self.save()

    @property
    def llm_context_messages_count(self) -> int:
        return self._config.getint("LLM", "context_messages_count")

    @llm_context_messages_count.setter
    def llm_context_messages_count(self, count):
        self._config.set("LLM", "context_messages_count", count)
        self.save()

    @property
    def azure_key(self) -> str:
        return self._config.get("Azure", "key")

    @azure_key.setter
    def azure_key(self, key):
        self._config.set("Azure", "key", key)
        self.save()

    @property
    def azure_region(self) -> str:
        return self._config.get("Azure", "region")

    @azure_region.setter
    def azure_region(self, region):
        self._config.set("Azure", "region", region)
        self.save()

    @property
    def azure_voice(self) -> str:
        return self._config.get("Azure", "voice")

    @azure_voice.setter
    def azure_voice(self, voice):
        self._config.set("Azure", "voice", voice)
        self.save()

    @property
    def elevenlabs_enabled(self) -> bool:
        return self._config.getboolean("ElevenLabs", "enabled")

    @elevenlabs_enabled.setter
    def elevenlabs_enabled(self, enabled):
        self._config.set("ElevenLabs", "enabled", enabled)
        self.save()

    @property
    def elevenlabs_key(self) -> str:
        return self._config.get("ElevenLabs", "key")

    @elevenlabs_key.setter
    def elevenlabs_key(self, key):
        self._config.set("ElevenLabs", "key", key)
        self.save()

    @property
    def elevenlabs_voice(self) -> str:
        return self._config.get("ElevenLabs", "voice")

    @elevenlabs_voice.setter
    def elevenlabs_voice(self, voice):
        self._config.set("ElevenLabs", "voice", voice)
        self.save()

    @property
    def discord_bot_api_key(self) -> str:
        return self._config.get("Discord", "bot_api_key")

    @discord_bot_api_key.setter
    def discord_bot_api_key(self, bot_api_key):
        self._config.set("Discord", "bot_api_key", bot_api_key)
        self.save()

    @property
    def llama_model_name(self) -> str:
        return self._config.get("LLaMA", "model_name")

    @llama_model_name.setter
    def llama_model_name(self, model_name):
        self._config.set("LLaMA", "model_name", model_name)
        self.save()

    @property
    def llama_search_path(self) -> str:
        return self._config.get("LLaMA", "search_path")

    @llama_search_path.setter
    def llama_search_path(self, search_path):
        self._config.set("LLaMA", "search_path", search_path)
        self.save()

    @property
    def bot_identity(self) -> str:
        return self._config.get("Bot", "identity")

    @bot_identity.setter
    def bot_identity(self, identity):
        self._config.set("Bot", "identity", identity)
        self.save()

    @property
    def bot_name(self) -> str:
        return self._config.get("Bot", "name")

    @bot_name.setter
    def bot_name(self, name):
        self._config.set("Bot", "name", name)
        self.save()

    @property
    def bot_speech_recognition_service(self) -> str:
        return self._config.get("Bot", "speech_recognition_service")

    @bot_speech_recognition_service.setter
    def bot_speech_recognition_service(self, service):
        self._config.set("Bot", "speech_recognition_service", service)
        self.save()

    @property
    def bot_tts_service(self) -> str:
        return self._config.get("Bot", "tts_service")

    @bot_tts_service.setter
    def bot_tts_service(self, service):
        self._config.set("Bot", "tts_service", service)
        self.save()

    @property
    def bot_llm(self) -> str:
        return self._config.get("Bot", "llm")

    @bot_llm.setter
    def bot_llm(self, llm):
        self._config.set("Bot", "llm", llm)
        self.save()

    @property
    def bot_blip_enabled(self) -> bool:
        return self._config.getboolean("Bot", "blip_enabled")

    @bot_blip_enabled.setter
    def bot_blip_enabled(self, enabled):
        self._config.set("Bot", "blip_enabled", "true" if enabled is True else "false")
        self.save()

    @property
    def bot_reminder(self):
        return self._config.get("Bot", "reminder")

    @bot_reminder.setter
    def bot_reminder(self, reminder):
        self._config.set("Bot", "reminder", reminder)
        self.save()

    @property
    def bot_initial_prompt(self):
        return self._config.get("Bot", "initial_prompt", fallback="Write {bot_name}'s next reply in a fictional chat between {bot_name} and {user_name}. Write 1 reply only in internet RP style, italicize actions, and avoid quotation marks. Be proactive, creative, and drive the plot and conversation forward. Write at least 1 paragraph, up to 4. Always stay in character and avoid repetition. {bot_identity} {user_identity}")

    @bot_initial_prompt.setter
    def bot_initial_prompt(self, initial_prompt):
        self._config.set("Bot", "initial_prompt", initial_prompt)
        self.save()

    @property
    def llm_temperature(self) -> float:
        return self._config.getfloat("LLM", "temperature")

    @llm_temperature.setter
    def llm_temperature(self, llm):
        self._config.set("LLM", "temperature", llm)
        self.save()

    @property
    def llm_presence_penalty(self) -> float:
        return self._config.getfloat("LLM", "presence_penalty")

    @llm_presence_penalty.setter
    def llm_presence_penalty(self, llm):
        self._config.set("LLM", "presence_penalty", llm)
        self.save()

    @property
    def llm_max_tokens(self) -> int:
        return self._config.getint("LLM", "max_tokens")

    @llm_max_tokens.setter
    def llm_max_tokens(self, max_tokens):
        self._config.set("LLM", "max_tokens", max_tokens)
        self.save()

    @property
    def llm_frequency_penalty(self) -> float:
        return self._config.getfloat("LLM", "frequency_penalty")

    @llm_frequency_penalty.setter
    def llm_frequency_penalty(self, frequency_penalty):
        self._config.set("LLM", "frequency_penalty", frequency_penalty)
        self.save()
