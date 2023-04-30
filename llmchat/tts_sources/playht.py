import discord

from . import TTSSource
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import io
import requests
import json

PLAYHT_API = "https://play.ht/api/v2"

class PlayHt(TTSSource):
    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(PlayHt, self).__init__(client, config, db)
        self._voice_list_cache = []

    @property
    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.config.playht_secret_key}",
            "X-USER-ID": self.config.playht_user_id,
        }

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        r = requests.post(f"{PLAYHT_API}/tts", data=json.dumps({
             "text": content,
             "voice": self.config.playht_voice_id
        }), headers=self.auth_headers | {
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }, stream=True)
        r.raise_for_status()

        def generate_audio() -> str:
            for data in r.iter_lines():
                if data:
                    data: str = data.decode("utf-8")
                    if not data.startswith("data: {"):
                        continue
                    
                    data = json.loads(data[5:])
                    if "error_message" in data:
                        raise Exception(f"Play.ht: {data['error_message']}")
                    
                    logger.debug(f"Play.ht progress: [{data['stage']}] {round(data['progress'] * 100)}%")
                    if "url" in data:
                        return data['url']
            return None

        audio_url = await self.client.loop.run_in_executor(None, generate_audio)
        if not audio_url:
            raise Exception("audio_url was None!")
        
        logger.debug(f"Downloading {audio_url}")
        data = await self.client.loop.run_in_executor(None, lambda: requests.get(audio_url))
        return io.BytesIO(data.content)

    def _get_all_voices(self):
        r = requests.get(f"{PLAYHT_API}/cloned-voices",
            headers=self.auth_headers | {
                "Accept": "application/json"
            })
        cloned_voices = r.json()
        if 'error_message' in cloned_voices:
            cloned_voices = []

        r = requests.get(f"{PLAYHT_API}/voices",
            headers=self.auth_headers | {
                "Accept": "application/json"
            })
        premade_voices = r.json()
        return cloned_voices + premade_voices
    
    def list_voices(self) -> list[discord.SelectOption]:
        self._voice_list_cache = self._get_all_voices()
        return [discord.SelectOption(value=v["id"], label=v["name"], default=self.config.playht_voice_id == v["id"],
                                     emoji=discord.PartialEmoji(name="♂️" if v["gender"] == "male" else "♀️") if "gender" in v else None,
                                     ) for i,v in enumerate(self._voice_list_cache)]

    def set_voice(self, voice_id: str) -> None:
        self.config.playht_voice_id = voice_id

    @property
    def current_voice_name(self) -> str:
        if self._voice_list_cache:
            for v in self._voice_list_cache:
                if v["id"] == self.config.playht_voice_id:
                    return v["name"]
            return self.config.playht_voice_id
        return self.config.playht_voice_id + " (voice id)"
