from . import SRSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
import speech_recognition as sr
from llmchat.logger import logger


class Azure(SRSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Azure, self).__init__(client, config, db)
        self.recognizer = sr.Recognizer()

    def recognize_speech(self, data: sr.AudioData):
        text, confidence = self.recognizer.recognize_azure(data, key=self.config.azure_key, location=self.config.azure_region)
        return text
