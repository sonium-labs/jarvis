"""
Real-time speech transcription module using Vosk.

This module provides continuous speech-to-text functionality with silence
detection for automatic termination. It uses the Vosk offline speech recognition
engine with a pre-loaded model for efficient, low-latency transcription.

Silence detection sensitivity is configurable. Initial values come from the
optional environment variables `VOSK_RMS_THRESHOLD` and
`VOSK_SILENCE_DURATION_SECONDS`. The `print_silence_config()` function,
called from Jarvis, displays these settings.
"""

import json
import time
import os

import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from dotenv import load_dotenv

import console_ui

load_dotenv() # Load environment variables for configurable settings

# --- Global Vosk Model and Recognizer Variables ---
model: Model | None = None
rec: KaldiRecognizer | None = None

# Suppress verbose Vosk logs early
SetLogLevel(-1)

# --- Configuration Constants ---
# Audio stream configuration
RATE = 16_000        # Sample rate in Hz: samples per second. Must match the Vosk model's expected rate.
CHUNK = 512          # Frames per buffer: number of audio frames processed at a time.
MAX_CHUNKS = int(6 * RATE / CHUNK) # Max recording chunks: approx. 6 seconds.

# Silence detection parameters (loaded from .env at module level, NO print here)
# Default values are used if environment variables are not set or invalid.
def_rms_threshold = 900
def_silence_duration = 1.5

try:
    RMS_THRESHOLD = int(os.getenv("VOSK_RMS_THRESHOLD", str(def_rms_threshold)))
except ValueError:
    console_ui.print_warning(f"Invalid VOSK_RMS_THRESHOLD in .env. Using default: {def_rms_threshold}")
    RMS_THRESHOLD = def_rms_threshold

try:
    SILENCE_DURATION_SECONDS = float(os.getenv("VOSK_SILENCE_DURATION_SECONDS", str(def_silence_duration)))
except ValueError:
    console_ui.print_warning(f"Invalid VOSK_SILENCE_DURATION_SECONDS in .env. Using default: {def_silence_duration}")
    SILENCE_DURATION_SECONDS = def_silence_duration

SILENCE_CHUNKS_END = int(SILENCE_DURATION_SECONDS * RATE / CHUNK)

def print_silence_config():
    """Prints the currently loaded silence detection parameters."""
    # Parameters are already loaded globally when the module is imported.
    # This function just prints them.
    console_ui.print_info(f"Silence detection: RMS Threshold={RMS_THRESHOLD}, Duration={SILENCE_DURATION_SECONDS:.1f}s ({SILENCE_CHUNKS_END} chunks)")

def initialize_vosk_model():
    """Initializes the Vosk model and recognizer with a progress bar."""
    global model, rec

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        transient=True # Progress bar disappears on completion/exit
    ) as progress:
        task = progress.add_task("[cyan]Preparing Vosk model...", total=100)

        # Simulate initial preparation steps (e.g., file checks, memory allocation simulation)
        simulated_prep_duration = 0.5  # Shorter simulation
        simulated_prep_steps = 5
        advance_per_prep_step = 2      # 5 steps * 2% = 10%

        for i in range(simulated_prep_steps):
            time.sleep(simulated_prep_duration / simulated_prep_steps)
            progress.update(task, advance=advance_per_prep_step)
            if i == simulated_prep_steps // 2:
                progress.update(task, description="[cyan]Checking Vosk components...")
            if progress.finished: return # Allow early exit

        # Actual model loading (progress is at 10% here)
        progress.update(task, description="[cyan]Loading main Vosk model data (this may take a moment)...", completed=10)
        try:
            model = Model("model") # Load the model from the 'model' directory
            progress.update(task, completed=80) # Model loaded, significant progress

            # Initialize recognizer (progress is at 80% here)
            progress.update(task, description="[cyan]Initializing Vosk recognizer...")
            rec = KaldiRecognizer(model, RATE)
            progress.update(task, completed=100) # Recognizer initialized, 100%
            progress.update(task, description="[green]Vosk setup complete!")

        except Exception as e:
            # Ensure progress bar completes and shows error
            progress.update(task, description=f"[red]Error during Vosk initialization: {e}", completed=100)
            model = None # Ensure model is None if loading failed
            rec = None   # And recognizer is also None
            return # Exit if any initialization fails

    # After 'with Progress' block automatically cleans up the progress bar
    if model and rec:
        console_ui.print_success("Vosk model and recognizer loaded successfully.")
    else:
        # This message will be shown if any of the returns were hit due to errors above.
        console_ui.print_error("Vosk initialization failed. Transcription will not be available. Jarvis may exit.")

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
    console_ui.print_info(f"Silence Duration updated to: {SILENCE_DURATION_SECONDS:.1f}s (SILENCE_CHUNKS_END: {SILENCE_CHUNKS_END})")

def record_and_transcribe(stream, initial_audio_buffer=None):
    """
    Record and transcribe audio from a PyAudio stream until silence is detected.
    Can be primed with an initial audio buffer.

    Args:
        stream: Active PyAudio input stream object.
        initial_audio_buffer (list[bytes], optional): Audio chunks to process before live stream.

    Yields:
        str: Partial transcriptions.
    Returns:
        str: Final transcribed text, or empty string if no speech was detected.
    """
    if not rec or not model: # Check both model and recognizer
        console_ui.print_error("Vosk model/recognizer not initialized. Cannot transcribe.")
        return ""

    rec.Reset()  # Reset the recognizer's state for a fresh transcription.

    if initial_audio_buffer:
        # console_ui.print_info(f"Processing {len(initial_audio_buffer)} pre-buffered audio chunks...") # Usually too verbose
        for chunk_data in initial_audio_buffer:
            if isinstance(chunk_data, bytes):
                rec.AcceptWaveform(chunk_data)
            else:
                console_ui.print_warning(f"Warning: Initial audio buffer contained non-bytes data: {type(chunk_data)}. Skipping this chunk.")
    
    silent_chunks_count = 0
    total_chunks_count = 0
    last_yielded_partial = ""

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        rec.AcceptWaveform(data)
        total_chunks_count += 1

        partial_result_json = rec.PartialResult()
        partial_text = json.loads(partial_result_json).get("partial", "").strip()

        if partial_text and partial_text != last_yielded_partial:
            yield partial_text
            last_yielded_partial = partial_text

        audio_i16 = np.frombuffer(data, dtype=np.int16)
        if audio_i16.size:
            rms = np.sqrt(np.mean(audio_i16.astype(np.float32)**2))
        else:
            rms = 0.0

        if rms < RMS_THRESHOLD:
            silent_chunks_count += 1
            if silent_chunks_count >= SILENCE_CHUNKS_END:
                break
        else:
            silent_chunks_count = 0

        if total_chunks_count >= MAX_CHUNKS:
            console_ui.print_warning("Maximum recording duration reached, stopping transcription.")
            break

    final_result_json = rec.FinalResult()
    final_text = json.loads(final_result_json).get("text", "").strip()
    
    return final_text
