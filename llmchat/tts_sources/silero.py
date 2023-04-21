import os.path

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

    def list_voices(self) -> list[str]:
        return sorted(['en_99', 'en_45', 'en_18', 'en_117', 'en_49', 'en_51', 'en_68', 'en_0',
                       'en_26', 'en_56', 'en_74', 'en_5', 'en_38', 'en_53', 'en_21', 'en_37',
                       'en_107', 'en_10', 'en_82', 'en_16', 'en_41', 'en_12', 'en_67', 'en_61',
                       'en_14', 'en_11', 'en_39', 'en_52', 'en_24', 'en_97', 'en_28', 'en_72',
                       'en_94', 'en_36', 'en_4', 'en_43', 'en_88', 'en_25', 'en_65', 'en_6',
                       'en_44', 'en_75', 'en_91', 'en_60', 'en_109', 'en_85', 'en_101', 'en_108',
                       'en_50', 'en_96', 'en_64', 'en_92', 'en_76', 'en_33', 'en_116', 'en_48',
                       'en_98', 'en_86', 'en_62', 'en_54', 'en_95', 'en_55', 'en_111', 'en_3',
                       'en_83', 'en_8', 'en_47', 'en_59', 'en_1', 'en_2', 'en_7', 'en_9',
                       'en_13', 'en_15', 'en_17', 'en_19', 'en_20', 'en_22', 'en_23', 'en_27',
                       'en_29', 'en_30', 'en_31', 'en_32', 'en_34', 'en_35', 'en_40', 'en_42',
                       'en_46', 'en_57', 'en_58', 'en_63', 'en_66', 'en_69', 'en_70', 'en_71',
                       'en_73', 'en_77', 'en_78', 'en_79', 'en_80', 'en_81', 'en_84', 'en_87',
                       'en_89', 'en_90', 'en_93', 'en_100', 'en_102', 'en_103', 'en_104', 'en_105',
                       'en_106', 'en_110', 'en_112', 'en_113', 'en_114', 'en_115'])

    def set_voice(self, voice_id: str) -> None:
        self.config.silero_voice = voice_id
