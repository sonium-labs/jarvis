# ─── wake-word listener (Porcupine) ───────────────────────────────────────
import pvporcupine
import numpy as np
import os
import collections
from dotenv import load_dotenv

load_dotenv()

# Initialize Porcupine
porcupine = None
try:
    porcupine = pvporcupine.create(
        access_key=os.getenv("PORCUPINE_KEY"),
        keywords=["jarvis"]
    )
except pvporcupine.PorcupineError as e:
    print(f"Failed to initialize Porcupine: {e}")
    # Handle error appropriately, e.g., raise an exception or exit

# Configuration for the rolling buffer
BUFFER_SECONDS = 1.0  # Duration of audio to buffer before wake word

# These will be defined properly if porcupine initializes
NUM_BUFFER_CHUNKS = 0
if porcupine:
    # Porcupine sample rate is fixed at 16000 Hz
    RATE = porcupine.sample_rate
    # Number of audio chunks to buffer
    NUM_BUFFER_CHUNKS = int(BUFFER_SECONDS * RATE / porcupine.frame_length)

def wait_for_wake_word(stream):
    """
    Block until the wake word is detected on the shared PyAudio stream.
    Returns a buffer of audio data (list of byte chunks) leading up to the wake word.
    Returns an empty list if Porcupine is not initialized or an error occurs.
    """
    if not porcupine:
        print("Error: Porcupine not initialized. Cannot listen for wake word.")
        return []

    audio_buffer = collections.deque(maxlen=NUM_BUFFER_CHUNKS)
    
    try:
        print(f"Listening for wake word (buffering ~{BUFFER_SECONDS:.1f}s of audio)...")
        while True:
            # Read audio data in chunks matching Porcupine's frame length
            pcm_bytes = stream.read(porcupine.frame_length,
                                    exception_on_overflow=False)
            
            # Add the raw audio bytes to our buffer
            audio_buffer.append(pcm_bytes)
            
            # Process the audio chunk with Porcupine
            # Convert bytes to int16 PCM samples
            pcm = np.frombuffer(pcm_bytes, dtype=np.int16)
            
            if porcupine.process(pcm) >= 0:
                print("Wake word detected!")
                return list(audio_buffer)  # Return the buffered audio chunks
    except Exception as e:
        print(f"Wake-word listening error: {e}")
        return [] # Return empty list on error
