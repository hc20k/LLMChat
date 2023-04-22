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

        audio_url = await self.client.loop.run_in_executor(None, generate_audio)
        
        assert audio_url
        logger.debug(f"Downloading {audio_url}")
        data = await self.client.loop.run_in_executor(None, lambda: requests.get(audio_url))
        return io.BytesIO(data.content)

    def list_voices(self) -> list[str]:
        r = requests.get(f"{PLAYHT_API}/voices",
            headers=self.auth_headers | {
                "Accept": "application/json"
            })
        j = r.json()
        return [v["id"] for v in j]
        

    def set_voice(self, voice_id: str) -> None:
        self.config.playht_voice_id = voice_id

    @property
    def current_voice_name(self) -> str:
        return self.config.playht_voice_id
