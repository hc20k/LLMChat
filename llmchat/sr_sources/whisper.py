from . import SRSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from speech_recognition import AudioData
import whisper
from llmchat.logger import logger
import numpy as np

class Whisper(SRSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Whisper, self).__init__(client, config, db)
        self.model = whisper.load_model("base", download_root="models/whisper/")

    def recognize_speech(self, data: AudioData):
        audio = np.frombuffer(data.get_raw_data(convert_rate=whisper.audio.SAMPLE_RATE),
                              np.int16).flatten().astype(np.float32) / 32768.0
        audio = whisper.pad_or_trim(audio)
        result = whisper.transcribe(self.model, audio=audio, language="en")
        result = result["text"].lstrip()
        if len(result) == 0:
            return None
        logger.debug("Said " + result)
        return result

    def unload(self):
        del self.model
