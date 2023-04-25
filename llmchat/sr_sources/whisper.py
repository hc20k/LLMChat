from . import SRSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from speech_recognition import AudioData
from transformers import WhisperForConditionalGeneration, WhisperProcessor, WhisperTokenizerFast
import torch
from llmchat.logger import logger
import numpy as np

class Whisper(SRSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Whisper, self).__init__(client, config, db)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading whisper model on {self.device}")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base.en", cache_dir="models/whisper").to(self.device)
        self.tokenizer = WhisperTokenizerFast.from_pretrained("openai/whisper-base.en", cache_dir="models/whisper")
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-base.en", cache_dir="models/whisper", tokenizer=self.tokenizer)

    def recognize_speech(self, data: AudioData):
        resampled = data.get_raw_data(convert_rate=16_000)
        resampled = np.frombuffer(resampled, dtype=np.int16).flatten().astype(np.float32) / 32768.0
        inputs = self.processor(resampled, return_tensors="pt", sampling_rate=16_000).input_features.to(self.device)
        predicted_ids = self.model.generate(inputs, max_length=480_000)
        decoded = self.processor.batch_decode(predicted_ids, skip_special_tokens=True, normalize=True)[0]
        return decoded

    def __del__(self):
        del self.model
        del self.processor
        torch.cuda.empty_cache()
