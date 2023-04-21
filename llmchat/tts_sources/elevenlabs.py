from . import TTSSource
from elevenlabs import generate, get_all_voices
import io
import asyncio


class ElevenLabs(TTSSource):
    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        data = await self.client.loop.run_in_executor(None, lambda: generate(content, self.config.elevenlabs_key, voice=self.config.elevenlabs_voice))
        buf = io.BytesIO(data)
        return buf

    @property
    def current_voice_name(self) -> str:
        return self.config.elevenlabs_voice

    def list_voices(self) -> list[str]:
        return [v.name for v in get_all_voices(self.config.elevenlabs_key)]

    def set_voice(self, voice_id: str) -> None:
        self.config.elevenlabs_voice = voice_id
