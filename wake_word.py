import pvporcupine
import pyaudio
import numpy as np
from dotenv import load_dotenv
import os

def wait_for_wake_word():
    load_dotenv()
    porcupine_key = os.getenv("PORCUPINE_KEY")
    porcupine = pvporcupine.create(access_key=porcupine_key, keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )

    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = np.frombuffer(pcm, dtype=np.int16)
            if porcupine.process(pcm) >= 0:
                break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()
