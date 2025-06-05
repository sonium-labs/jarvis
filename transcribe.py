"""
Real-time speech transcription module using Vosk.

This module provides continuous speech-to-text functionality with silence detection
for automatic termination. It uses the Vosk offline speech recognition engine
with a pre-loaded model for efficient, low-latency transcription.
"""

import json
import numpy as np

import sys, threading, time

# Audio stream configuration constants
RATE = 16_000        # Sample rate in Hz, must match model's expected rate
CHUNK = 512          # Number of frames per buffer - smaller values reduce latency

def _spinner(msg=""):
    spinner = "|/-\\"
    idx = 0
    while not getattr(threading.current_thread(), "stop_spinner", False):
        print(f"\r{msg} {spinner[idx % len(spinner)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (len(msg) + 2) + "\r", end="", flush=True)

# Start spinner in a thread
spinner_thread = threading.Thread(target=_spinner)
spinner_thread.start()

# Initialize Vosk components (done once at module load for performance)
from vosk import Model, KaldiRecognizer
model = Model("model")                # Load speech recognition model into memory
rec = KaldiRecognizer(model, RATE)   # Create persistent recognition object

# Stop spinner
spinner_thread.stop_spinner = True
spinner_thread.join()
print("Model loaded.")

# Silence detection configuration
RMS_THRESHOLD = 900               # Root Mean Square amplitude threshold for silence detection
SILENCE_CHUNKS_END = int(1.2 * RATE / CHUNK)   # Number of silent chunks before stopping (~1.2 seconds)
MAX_CHUNKS = int(6 * RATE / CHUNK)             # Maximum recording duration (6 seconds)

def record_and_transcribe(stream):
    """
    Record and transcribe audio from a PyAudio stream until silence is detected.

    The function implements a simple silence detection algorithm based on RMS amplitude
    and automatically stops recording when either:
    1. The specified duration of silence is detected (SILENCE_CHUNKS_END)
    2. The maximum recording duration is reached (MAX_CHUNKS)

    Args:
        stream: PyAudio stream object configured with matching RATE and CHUNK settings

    Returns:
        str: Transcribed text, or empty string if no speech was detected

    Implementation details:
        - Continuously feeds audio chunks to Vosk recognizer
        - Calculates RMS amplitude for silence detection
        - Maintains silence and total chunk counters for termination conditions
    """
    rec.Reset()                  # Clear any previous recognition state
    silent = 0                  # Counter for consecutive silent chunks
    total = 0                   # Counter for total chunks processed
    last_partial = ""           # Last partial transcription (not used in final result)

    while True:
        # Read audio chunk from stream (non-blocking to prevent buffer overflow)
        data = stream.read(CHUNK, exception_on_overflow=False)
        rec.AcceptWaveform(data)    # Feed audio data to Vosk recognizer
        total += 1
        
        # ----- Partial result streaming -----
        partial_json = json.loads(rec.PartialResult())
        partial = partial_json.get("partial", "").strip()
        if partial and partial != last_partial:
            yield partial                # stream out new words
            last_partial = partial

        # Convert audio data to numpy array for RMS calculation
        audio_i16 = np.frombuffer(data, dtype=np.int16)
        if audio_i16.size:
            # Calculate Root Mean Square amplitude of the audio chunk
            rms = np.sqrt(np.mean(audio_i16.astype(np.float32)**2))
        else:
            rms = 0.0          # Handle empty chunks gracefully

        # Silence detection logic
        if rms < RMS_THRESHOLD:
            silent += 1
            if silent >= SILENCE_CHUNKS_END:
                break          # Stop if silence threshold duration is reached
        else:
            silent = 0        # Reset silence counter on detecting sound

        # Safety timeout to prevent infinite recording
        if total >= MAX_CHUNKS:
            break

    # Extract transcribed text from Vosk's JSON result
    result = json.loads(rec.FinalResult())
    return result.get("text", "").strip()
