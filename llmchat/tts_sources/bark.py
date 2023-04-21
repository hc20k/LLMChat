import bark.generation

from . import TTSSource
import io
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
from bark import SAMPLE_RATE, generate_audio, preload_models
import asyncio

bark.generation.CACHE_DIR = "models/bark/"

class Bark(TTSSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Bark, self).__init__(client, config, db)
        self.client.loop.run_in_executor(None, lambda: preload_models())

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        data = await self.client.loop.run_in_executor(None, lambda: generate_audio(content))
        return io.BytesIO(data.tobytes())

    def list_voices(self) -> list[str]:
        return []
