import os.path

import discord

from . import TTSSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import torch
import torchaudio
import io


class SileroTTS(TTSSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(SileroTTS, self).__init__(client, config, db)
        device = torch.device('cpu') if not torch.cuda.is_available() else torch.device('cuda')
        if not os.path.isdir("models/torch/"):
            os.mkdir("models/torch/")
        torch.hub.set_dir("models/torch/")
        self.model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='en', speaker="v3_en", device=device)
        logger.info("Silero loaded.")

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        audio: torch.Tensor = await self.client.loop.run_in_executor(None, lambda: self.model.apply_tts(text=content, sample_rate=48000, speaker=self.config.silero_voice))
        audio = audio.unsqueeze(0)
        buf = io.BytesIO()
        torchaudio.save(buf, audio, 48000, format="wav")
        buf.seek(0)
        return buf

    @property
    def current_voice_name(self) -> str:
        return self.config.silero_voice

    def list_voices(self) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=v, value=v) for v in [f"en_{n}" for n in range(0, 118)]] # 117 voices

    def set_voice(self, voice_id: str) -> None:
        self.config.silero_voice = voice_id
