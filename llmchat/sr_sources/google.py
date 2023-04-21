from . import SRSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
import speech_recognition as sr
from llmchat.logger import logger


class Google(SRSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Google, self).__init__(client, config, db)
        self.recognizer = sr.Recognizer()

    def recognize_speech(self, data: sr.AudioData):
        return self.recognizer.recognize_google(data)

    def __del__(self):
        del self.recognizer
