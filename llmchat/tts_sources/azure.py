import asyncio

import azure.cognitiveservices.speech
import discord

from . import TTSSource
import azure.cognitiveservices.speech as speechsdk
from discord import User, Client, SelectOption
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import io


class Azure(TTSSource):
    synthesizer: speechsdk.speech.SpeechSynthesizer

    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Azure, self).__init__(client, config, db)
        logger.info("Logging into Azure...")
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_key, region=self.config.azure_region
        )
        self.synthesizer = speechsdk.speech.SpeechSynthesizer(self.speech_config, None)

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        self.speech_config.speech_synthesis_voice_name = self.config.azure_voice
        self.synthesizer = speechsdk.speech.SpeechSynthesizer(self.speech_config, None)
        result: speechsdk.SpeechSynthesisResult = await self.client.loop.run_in_executor(None, lambda: self.synthesizer.speak_text(content))
        buf = io.BytesIO(result.audio_data)
        return buf

    @property
    def current_voice_name(self) -> str:
        return self.config.azure_voice

    def set_voice(self, voice_id: str):
        self.config.azure_voice = voice_id

    def list_voices(self) -> list[SelectOption]:
        res: speechsdk.speech.SynthesisVoicesResult = self.synthesizer.get_voices_async("en-US").get()
        return [SelectOption(label=v.local_name, value=v.short_name, default=self.config.azure_voice == v.short_name,
                             emoji=discord.PartialEmoji(name="♂️" if v.gender == azure.cognitiveservices.speech.SynthesisVoiceGender.Male else "♀️")) for v in res.voices]
