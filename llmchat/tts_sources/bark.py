import bark.generation
import discord

from . import TTSSource
import io
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
from bark import SAMPLE_RATE, generate_audio, preload_models
from bark.generation import models
from scipy.io.wavfile import write as write_wav
import os

bark.generation.CACHE_DIR = "models/bark/"
bark.generation.REMOTE_MODEL_PATHS = {
    "text": {
        "path": os.environ.get("SUNO_TEXT_MODEL_PATH", os.path.join(bark.generation.REMOTE_BASE_URL, "text.pt")),
        "checksum": "b3e42bcbab23b688355cd44128c4cdd3"
    },
    "coarse": {
        "path": os.environ.get("SUNO_COARSE_MODEL_PATH", os.path.join(bark.generation.REMOTE_BASE_URL, "coarse.pt")),
        "checksum": "5fe964825e3b0321f9d5f3857b89194d"
    },
    "fine": {
        "path": os.environ.get("SUNO_FINE_MODEL_PATH", os.path.join(bark.generation.REMOTE_BASE_URL, "fine.pt")),
        "checksum": "5428d1befe05be2ba32195496e58dc90"
    }
}


class Bark(TTSSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Bark, self).__init__(client, config, db)
        self.client.loop.run_in_executor(None, lambda: preload_models())

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        data = await self.client.loop.run_in_executor(None, lambda: generate_audio(content))
        buf = io.BytesIO()
        write_wav(buf, SAMPLE_RATE, data)
        return buf

    def list_voices(self) -> list[discord.SelectOption]:
        return []

    def __del__(self):
        logger.info("Unloading models...")
        for m in models:
            model = models[m]
            del model