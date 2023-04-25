import discord
import speech_recognition as sr
import pyaudio
import numpy as np
import asyncio
from logger import logger
from sr_sources import SRSource

class DummyAudioSource(sr.AudioSource):
    class DummyStream(object):
        def __init__(self, buffer_sink):
            self.buffer_sink = buffer_sink

        def read(self, size):
            bytes_to_read = min(size, len(self.buffer_sink.buffer))
            ret = self.buffer_sink.buffer.tobytes()[:bytes_to_read]
            self.buffer_sink.buffer = self.buffer_sink.buffer[bytes_to_read:]
            return ret

        def close(self):
            pass

    def __init__(self, buffer_sink):
        self.buffer_sink: BufferAudioSink = buffer_sink
        self.SAMPLE_RATE = discord.opus.Decoder.SAMPLING_RATE
        self.CHUNK = self.buffer_sink.buffer_size
        self.SAMPLE_WIDTH = 2

        self.audio = pyaudio.PyAudio()
        self.stream = None

    def __enter__(self):
        # FIX: For some reason this only works when the sample rate is divided by 2... Otherwise the audio's super slow.
        self.stream = self.audio.open(channels=2, rate=round(discord.opus.Decoder.SAMPLING_RATE/2),
                                      frames_per_buffer=discord.opus.Decoder.FRAME_SIZE, format=pyaudio.paInt16, input=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.audio.terminate()


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
        self.buffer_size = discord.opus.Decoder.FRAME_SIZE
        self.buffer = np.zeros(shape=(self.buffer_size, self.NUM_CHANNELS), dtype='int16')
        self.speaker = None
        self.is_speaking = False

        self.stream = DummyAudioSource(self)
        self.sr = sr.Recognizer()
        self.sr.non_speaking_duration = 0.1
        self.sr.pause_threshold = 0.3
        self.stop_listen = self.sr.listen_in_background(self.stream, self.listen)

    def listen(self, _, audio_data: sr.AudioData):
        if self.is_speaking or not self.speaker:
            return

        debug = False
        if debug:
            import sounddevice as sd
            sd.play(np.frombuffer(audio_data.get_raw_data(), dtype='int16'), self.SAMPLE_RATE_HZ)

        try:
            result = self.sr_source.recognize_speech(audio_data)
            if result is not None:
                logger.info(f"Said: {result}")
                self.loop.create_task(self.on_speech(self.speaker, result))
        except Exception as e:
            logger.warn("Exception thrown while processing audio. " + str(e))

    def cleanup(self):
        self.on_leave()

    def on_leave(self):
        logger.debug("Cleaning up")
        self.stop_listen()

    def on_rtcp(self, packet: discord.RTCPPacket):
        pass

    def on_audio(self, voice_data: discord.AudioFrame):
        if voice_data.user is None:
            return

        # adapted from https://github.com/vadimkantorov/discordspeechtotext/
        self.speaker = voice_data.user.id
        frame = np.ndarray(shape=(self.NUM_SAMPLES, self.NUM_CHANNELS), dtype='int16', buffer=voice_data.audio)
        speaking = np.abs(frame).sum() > 0

        if speaking and not self.is_speaking:
            if self.buffer_pointer + self.NUM_SAMPLES >= self.buffer_size:
                # Shift the buffer to the left by NUM_SAMPLES
                self.buffer[:self.buffer_size - self.NUM_SAMPLES] = self.buffer[self.NUM_SAMPLES:]
                self.buffer_pointer = self.buffer_size - self.NUM_SAMPLES

            # Add the new frame to the buffer
            self.buffer[self.buffer_pointer:self.buffer_pointer + self.NUM_SAMPLES] = frame
            self.buffer_pointer += self.NUM_SAMPLES
