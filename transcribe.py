"""
Real-time speech transcription module using Vosk.

This module provides continuous speech-to-text functionality with silence detection
for automatic termination. It uses the Vosk offline speech recognition engine
with a pre-loaded model for efficient, low-latency transcription.
"""

import json
import time
import threading

import numpy as np
from vosk import Model, KaldiRecognizer # Moved Vosk import to the top

# --- Configuration Constants ---
# Audio stream configuration
RATE = 16_000        # Sample rate in Hz: samples per second. Must match the Vosk model's expected rate.
CHUNK = 512          # Frames per buffer: number of audio frames processed at a time. Smaller values can reduce latency but increase CPU load.

# Silence detection configuration
RMS_THRESHOLD = 900               # RMS amplitude: threshold below which audio is considered silent.
SILENCE_CHUNKS_END = int(1.2 * RATE / CHUNK)   # Silent chunks to stop: number of consecutive silent chunks before transcription stops (approx. 1.2 seconds).
MAX_CHUNKS = int(6 * RATE / CHUNK)             # Max recording chunks: maximum number of chunks to record before stopping (approx. 6 seconds).

# --- Vosk Model Loading with Spinner ---
_model_load_event = threading.Event() # Event to signal spinner thread to stop

def _spinner_worker(event, msg="Loading Vosk model..."):
    """Displays a simple CLI spinner until the event is set."""
    spinner_chars = "|/-\\"
    idx = 0
    while not event.is_set():
        print(f"\r{msg} {spinner_chars[idx % len(spinner_chars)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (len(msg) + 2) + "\r", end="", flush=True) # Clear spinner line

print("Initializing Vosk model (this may take a moment)...")
_spinner_thread = threading.Thread(target=_spinner_worker, args=(_model_load_event,))
_spinner_thread.start()

# Initialize Vosk components (done once at module load for performance)
model = Model("model")  # Loads the speech recognition model from the 'model' directory.
                        # This can be memory-intensive and take time on first load.
rec = KaldiRecognizer(model, RATE)  # Creates a recognizer instance, configured for the model and sample rate.
                                    # This object will be used for all subsequent transcriptions.

_model_load_event.set() # Signal spinner to stop
_spinner_thread.join()  # Wait for spinner thread to finish
print("Vosk model loaded successfully.")

def record_and_transcribe(stream, initial_audio_buffer=None):
    """
    Record and transcribe audio from a PyAudio stream until silence is detected.
    Can be primed with an initial audio buffer.

    Args:
        stream: Active PyAudio input stream object, configured with RATE and CHUNK settings
                matching those used by the Vosk KaldiRecognizer.
        initial_audio_buffer (list[bytes], optional): A list of raw audio byte chunks
                                                      (each typically `CHUNK` size) to be processed
                                                      before reading from the live stream.
                                                      Useful for prepending audio, like from a wake word buffer.
                                                      Defaults to None.
    Yields:
        str: Partial transcriptions.
    Returns:
        str: Final transcribed text, or empty string if no speech was detected.
    """
    rec.Reset()  # Reset the recognizer's state to ensure a fresh transcription.

    # Prime the recognizer with the initial audio buffer if one is provided.
    # This is useful for including audio captured just before a command starts (e.g., rolling wake word buffer).
    if initial_audio_buffer:
        print(f"Processing {len(initial_audio_buffer)} pre-buffered audio chunks...")
        for chunk_data in initial_audio_buffer:
            if isinstance(chunk_data, bytes):
                rec.AcceptWaveform(chunk_data)  # Feed each chunk from the buffer to Vosk.
            else:
                # This case should ideally not be reached if wake_word.py correctly returns a list of bytes.
                print(f"Warning: Initial audio buffer contained non-bytes data: {type(chunk_data)}. Skipping this chunk.")
    
    silent_chunks_count = 0  # Counter for consecutive chunks of audio below the RMS silence threshold.
    total_chunks_count = 0   # Counter for the total number of chunks processed from the live stream.
    last_yielded_partial = "" # Stores the last partial result yielded to avoid redundant yields of the same text.

    while True:
        # Read an audio chunk from the live stream.
        # exception_on_overflow=False prevents PyAudio from raising an error if its internal buffer overflows,
        # which can happen if Python's processing loop doesn't keep up with the audio input rate.
        # Instead, older, unread data is silently discarded by PyAudio.
        data = stream.read(CHUNK, exception_on_overflow=False)
        rec.AcceptWaveform(data)    # Feed the live audio data to the Vosk recognizer.
        total_chunks_count += 1
        
        # ----- Partial result streaming -----
        # Check for and yield partial transcription results for live feedback.
        partial_result_json = rec.PartialResult() # Get current partial result from Vosk (as JSON string).
        partial_text = json.loads(partial_result_json).get("partial", "").strip()
        
        if partial_text and partial_text != last_yielded_partial:
            yield partial_text  # Stream out new words as they are recognized.
            last_yielded_partial = partial_text

        # Convert audio data to numpy array for RMS calculation
        audio_i16 = np.frombuffer(data, dtype=np.int16)
        if audio_i16.size:
            # Calculate Root Mean Square (RMS) amplitude of the audio chunk to detect silence.
            # Convert to float32 to prevent overflow during squaring and for precision in mean calculation.
            rms = np.sqrt(np.mean(audio_i16.astype(np.float32)**2))
        else:
            rms = 0.0  # Consider empty chunks (e.g., if stream.read returned no data) as silent.

        # Silence detection logic:
        if rms < RMS_THRESHOLD:  # If the chunk's RMS is below the silence threshold.
            silent_chunks_count += 1
            if silent_chunks_count >= SILENCE_CHUNKS_END: # If enough consecutive silent chunks are detected.
                print("\nSilence detected, stopping transcription.")
                break  # Stop recording and transcribing.
        else:
            silent_chunks_count = 0  # Reset silence counter if sound is detected (RMS >= threshold).

        # Safety timeout: Stop recording if it exceeds the maximum configured duration.
        if total_chunks_count >= MAX_CHUNKS:
            print("\nMaximum recording duration reached, stopping transcription.")
            break

    # After the loop (due to silence or max duration), get the final transcription result.
    final_result_json = rec.FinalResult()  # Get the definitive final result from Vosk (as JSON string).
    final_text = json.loads(final_result_json).get("text", "").strip()

    # Yield the final text if it contains additional words that were not part of
    # the last partial result so callers iterating over this generator receive
    # the complete transcription.
    if final_text and final_text != last_yielded_partial:
        yield final_text

    return final_text  # Return the fully transcribed text, or an empty string if no speech was recognised.
