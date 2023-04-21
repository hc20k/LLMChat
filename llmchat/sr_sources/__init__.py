from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from speech_recognition import AudioData
from typing import Union

class SRSource:
    def __init__(self, client: Client, config: Config, db: PersistentData):
        self.config = config
        self.db = db
        self.client = client

    def recognize_speech(self, data: AudioData) -> Union[str, None]:
        return NotImplementedError()

    async def unload(self):
        pass