# ─── wake-word listener (Porcupine) ───────────────────────────────────────
import pvporcupine, numpy as np, os
from dotenv import load_dotenv

load_dotenv()
porcupine = pvporcupine.create(
    access_key=os.getenv("PORCUPINE_KEY"),
    keywords=["jarvis"]
)

def wait_for_wake_word(stream):
    """Block until the wake word is detected on the shared PyAudio stream."""
    try:
        while True:
            pcm_bytes = stream.read(porcupine.frame_length,
                                    exception_on_overflow=False)
            pcm = np.frombuffer(pcm_bytes, dtype=np.int16)
            if porcupine.process(pcm) >= 0:
                return
    except Exception as e:
        print("Wake-word error:", e)
