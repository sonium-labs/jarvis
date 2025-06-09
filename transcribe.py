"""
Real-time speech transcription module using Vosk.

This module provides continuous speech-to-text functionality with silence
detection for automatic termination. It uses the Vosk offline speech recognition
engine with a pre-loaded model for efficient, low-latency transcription.

Silence detection sensitivity is configurable. Initial values come from the
optional environment variables `VOSK_RMS_THRESHOLD` and
`VOSK_SILENCE_DURATION_SECONDS`, and Jarvis lets you adjust them at startup.
"""

import json
import time

import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
import console_ui
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables for configurable settings

# --- Configuration Constants ---
# Audio stream configuration
RATE = 16_000        # Sample rate in Hz: samples per second. Must match the Vosk model's expected rate.
CHUNK = 512          # Frames per buffer: number of audio frames processed at a time. Smaller values can reduce latency but increase CPU load.

# Silence detection configuration (configurable via .env)
RMS_THRESHOLD = int(os.getenv("VOSK_RMS_THRESHOLD", "900"))
SILENCE_DURATION_SECONDS = float(os.getenv("VOSK_SILENCE_DURATION_SECONDS", "1.2"))
SILENCE_CHUNKS_END = int(SILENCE_DURATION_SECONDS * RATE / CHUNK)
console_ui.print_info(f"Silence detection: RMS Threshold={RMS_THRESHOLD}, Duration={SILENCE_DURATION_SECONDS}s")
MAX_CHUNKS = int(6 * RATE / CHUNK)             # Max recording chunks: maximum number of chunks to record before stopping (approx. 6 seconds).

# --- Vosk Model Loading with Rich Progress ---
# Suppress verbose Vosk logs
SetLogLevel(-1)

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    transient=True
) as progress:
    task = progress.add_task("[cyan]Preparing Vosk model...", total=100)

    # Simulate initial preparation steps for a smoother start (e.g., 1.5 seconds, up to 60%)
    simulated_prep_duration = 1.5  # seconds
    simulated_prep_steps = 15      # number of small updates
    advance_per_prep_step = 4      # 15 steps * 4% = 60%

    for i in range(simulated_prep_steps):
        time.sleep(simulated_prep_duration / simulated_prep_steps)
        progress.update(task, advance=advance_per_prep_step)
        if i == simulated_prep_steps // 2:
            progress.update(task, description="[cyan]Loading Vosk components...")
        if progress.finished: # Allow early exit if progress is cancelled
            break
    
    if not progress.finished:
        # Actual model loading (progress is at 60% here)
        progress.update(task, description="[cyan]Loading main Vosk model data (this may take a moment)...", completed=60) # Ensure it's exactly 60
        model = Model("model")
        # Model loading finished, now at 99%
        progress.update(task, completed=99)
        # Make the 99% state visible for a short duration
        if not progress.finished: # Check again in case of quick cancellation
            time.sleep(0.3) # Pause for 0.3 seconds to show 99%

    if not progress.finished:
        # Recognizer initialization (progress is at 99% here)
        progress.update(task, description="[cyan]Initializing recognizer...")
        rec = KaldiRecognizer(model, RATE)
        progress.update(task, completed=100) # Set progress to 100%
console_ui.print_success("Vosk model loaded successfully.")

# --- Silence Detection Getters and Setters ---
def get_rms_threshold() -> int:
    """Returns the current RMS threshold for silence detection."""
    return RMS_THRESHOLD

def get_silence_duration_seconds() -> float:
    """Returns the current silence duration in seconds."""
    return SILENCE_DURATION_SECONDS

def set_rms_threshold(new_threshold: int):
    """Sets a new RMS threshold for silence detection."""
    global RMS_THRESHOLD
    RMS_THRESHOLD = new_threshold
    console_ui.print_info(f"RMS Threshold updated to: {RMS_THRESHOLD}")

def set_silence_duration(new_duration_seconds: float):
    """Sets a new silence duration (in seconds) and recalculates SILENCE_CHUNKS_END."""
    global SILENCE_DURATION_SECONDS, SILENCE_CHUNKS_END
    SILENCE_DURATION_SECONDS = new_duration_seconds
    SILENCE_CHUNKS_END = int(SILENCE_DURATION_SECONDS * RATE / CHUNK)
    console_ui.print_info(f"Silence Duration updated to: {SILENCE_DURATION_SECONDS}s (SILENCE_CHUNKS_END: {SILENCE_CHUNKS_END})")

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
        console_ui.print_info(f"Processing {len(initial_audio_buffer)} pre-buffered audio chunks...")
        for chunk_data in initial_audio_buffer:
            if isinstance(chunk_data, bytes):
                rec.AcceptWaveform(chunk_data)  # Feed each chunk from the buffer to Vosk.
            else:
                # This case should ideally not be reached if wake_word.py correctly returns a list of bytes.
                console_ui.print_warning(f"Warning: Initial audio buffer contained non-bytes data: {type(chunk_data)}. Skipping this chunk.")
    
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
                break  # Stop recording and transcribing.
        else:
            silent_chunks_count = 0  # Reset silence counter if sound is detected (RMS >= threshold).

        # Safety timeout: Stop recording if it exceeds the maximum configured duration.
        if total_chunks_count >= MAX_CHUNKS:
            console_ui.print_warning("Maximum recording duration reached, stopping transcription.")
            break

    # After the loop (due to silence or max duration), get the final transcription result.
    final_result_json = rec.FinalResult() # Get the definitive final result from Vosk (as JSON string).
    final_text = json.loads(final_result_json).get("text", "").strip()
    
    return final_text  # Return the fully transcribed text, or an empty string if no speech was recognized.
