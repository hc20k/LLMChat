import discord
import speech_recognition as sr
import pyaudio
import whisper
import numpy as np
import asyncio
from logger import logger

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
    def __init__(self, on_speech, on_error, whisper_ctx):
        self.on_speech = on_speech
        self.on_error = on_error

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

        self.whisper: whisper.Whisper = whisper_ctx

    def listen(self, _, audio_data: sr.AudioData):
        if self.is_speaking:
            return

        debug = False
        if debug:
            import sounddevice as sd
            sd.play(np.frombuffer(audio_data.get_raw_data(), dtype='int16'), self.SAMPLE_RATE_HZ)

        if not self.whisper:
            try:
                result = self.sr.recognize_google(audio_data)
                logger.debug("Said " + str(result))
                asyncio.run(self.on_speech(self.speaker, result))
            except sr.exceptions.TranscriptionFailed:
                logger.error("Failed to transcribe.")
                asyncio.run(self.on_error())
            except sr.exceptions.UnknownValueError:
                logger.error("SR doesn't understand.")
                asyncio.run(self.on_error())
            except Exception as e:
                logger.error("Exception thrown while processing audio. " + str(e))
        else:
            audio = np.frombuffer(audio_data.get_raw_data(convert_rate=whisper.audio.SAMPLE_RATE),
                                  np.int16).flatten().astype(np.float32) / 32768.0
            audio = whisper.pad_or_trim(audio)
            result = whisper.transcribe(self.whisper, audio=audio, language="en")
            result = result["text"].lstrip()
            if len(result) == 0:
                return
            logger.debug("Said " + result)
            asyncio.run(self.on_speech(self.speaker, result))

    def cleanup(self):
        logger.debug("Cleaning up")
        # self.stop_listen(wait_for_stop=True)

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
