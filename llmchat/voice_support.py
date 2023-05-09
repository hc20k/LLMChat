import threading
import discord
import speech_recognition
import speech_recognition as sr
import pyaudio
import numpy as np
import asyncio
from logger import logger
from sr_sources import SRSource
import time

class BufferAudioSink(discord.AudioSink):
    sr_source: SRSource
    def __init__(self, sr_source: SRSource, on_speech, loop: asyncio.BaseEventLoop):
        self.on_speech = on_speech
        self.sr_source = sr_source
        self.loop = loop

        self.NUM_CHANNELS = discord.opus.Decoder.CHANNELS
        self.NUM_SAMPLES = discord.opus.Decoder.SAMPLES_PER_FRAME
        self.SAMPLE_RATE_HZ = discord.opus.Decoder.SAMPLING_RATE

        self.buffer_pointer = 0
        self.buffer_size = discord.opus.Decoder.SAMPLING_RATE * 5
        self.buffer = np.zeros(shape=(self.buffer_size, self.NUM_CHANNELS), dtype='int16')
        self.speaker = None
        self.is_speaking = False
        self._last_spoke = time.time()
        self.silence_limit = 1.5  # seconds

        # self.stream = DummyAudioSource(self)
        self.sr = sr.Recognizer()
        self.slience_thread = threading.Thread(target=self.check_silence)
        self.slience_thread.start()
        # self.sr.non_speaking_duration = 0.1
        # self.sr.pause_threshold = 0.3
        # self.stop_listen = self.sr.listen_in_background(self.stream, self.listen)

    def listen(self, _, audio_data: sr.AudioData):
        if self.is_speaking or not self.speaker:
            return

        debug = True
        if debug:
            import sounddevice as sd
            sd.play(np.frombuffer(audio_data.get_raw_data(), dtype='int16'), self.SAMPLE_RATE_HZ)

        try:
            logger.info("Recognizing speech...")
            result = self.sr_source.recognize_speech(audio_data)
            if result:
                logger.info(f"Said: {result}")
                self.loop.create_task(self.on_speech(self.speaker, result))
        except Exception as e:
            logger.warn("Exception thrown while processing audio. " + str(e))
            raise e

    def recognize_buffer(self):
        self.is_speaking = True
        speech_data = speech_recognition.AudioData(self.buffer[:self.buffer_pointer], self.SAMPLE_RATE_HZ * 2, discord.opus.Decoder.CHANNELS)

        try:
            logger.info("Recognizing speech...")
            result = self.sr_source.recognize_speech(speech_data)
            if result:
                logger.info(f"Said: {result}")
                self.loop.create_task(self.on_speech(self.speaker, result))
        except BaseException as e:
            self.is_speaking = False
            logger.warn("Exception thrown while processing audio. " + str(e))
            raise e

        self.buffer_pointer = 0
        self.buffer = np.zeros(shape=(self.buffer_size, self.NUM_CHANNELS), dtype='int16')  # clear

    def cleanup(self):
        pass

    def on_rtcp(self, packet: discord.RTCPPacket):
        pass

    @property
    def time_since_last_spoke(self):
        return time.time() - self._last_spoke

    def check_silence(self):
        while 1:
            if self.time_since_last_spoke > self.silence_limit and np.abs(self.buffer).max() > 0:
                self._last_spoke = time.time()
                self.recognize_buffer()
            time.sleep(0.1)

    def on_audio(self, voice_data: discord.AudioFrame):
        if voice_data.user is None:
            return

        # adapted from https://github.com/vadimkantorov/discordspeechtotext/
        self.speaker = voice_data.user.id
        frame = np.ndarray(shape=(self.NUM_SAMPLES, self.NUM_CHANNELS), dtype='int16', buffer=voice_data.audio)
        speaking = np.abs(frame).max() > 10

        if speaking and not self.is_speaking:
            self._last_spoke = time.time()
            if self.buffer_pointer + self.NUM_SAMPLES >= self.buffer_size:
                # buffer is full, flush
                self.recognize_buffer()

            # Add the new frame to the buffer
            self.buffer[self.buffer_pointer:self.buffer_pointer + self.NUM_SAMPLES] = frame
            self.buffer_pointer += self.NUM_SAMPLES
