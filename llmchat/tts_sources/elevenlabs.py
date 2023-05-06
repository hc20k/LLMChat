import os

import discord

from . import TTSSource
from elevenlabs import Voice, generate, voices, is_voice_id, api, set_api_key
from discord import SelectOption
import io
import asyncio


class ElevenLabs(TTSSource):
    voice_cache: list[Voice] = None
    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        set_api_key(self.config.elevenlabs_voice)
        data = await self.client.loop.run_in_executor(None, lambda: generate(content, api_key=self.config.elevenlabs_key, voice=self.config.elevenlabs_voice))
        buf = io.BytesIO(data)
        return buf

    @property
    def current_voice_name(self) -> str:
        if is_voice_id(self.config.elevenlabs_voice):
            for v in self.voice_cache or voices(self.config.elevenlabs_key):
                if v.voice_id == self.config.elevenlabs_voice:
                    return v.name
            return "Unknown"
        return self.config.elevenlabs_voice

    def list_voices(self) -> list[SelectOption]:
        self.voice_cache = voices(self.config.elevenlabs_key)
        return [SelectOption(label=v.name, value=v.voice_id, default=self.config.elevenlabs_voice == v.voice_id,
                             emoji=discord.PartialEmoji(name="⚙️") if v.category != "premade" else None) for v in self.voice_cache]

    def set_voice(self, voice_id: str) -> None:
        self.config.elevenlabs_voice = voice_id
