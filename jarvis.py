"""
Main Jarvis voice assistant orchestrator.

This module coordinates the voice assistant's core functionality, including:
- Wake word detection
- Speech-to-text transcription
- Command interpretation
- Text-to-speech response
- Music control via REST API integration

The assistant maintains a single shared microphone stream for efficiency
and provides voice control over a remote music bot service.
"""

import os
import queue
import threading

import pyaudio
import pyttsx3
import requests
from dotenv import load_dotenv

from transcribe import record_and_transcribe, get_rms_threshold, set_rms_threshold, get_silence_duration_seconds, set_silence_duration
from wake_word import wait_for_wake_word
import console_ui

# Initialize environment variables and global service objects
load_dotenv()                                 # Load configuration from .env file

# Global flag controlling whether text-to-speech is active
TTS_ENABLED = True

# ─── async, interruptible text-to-speech ────────────────────────────────
class AsyncTTS:
    """Threaded pyttsx3 wrapper with optional global enable/disable."""

    def __init__(self):
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)  # daemon=True allows main program to exit even if thread is running
        self._thread.start()

    def _worker(self):
        """Dedicated worker thread for pyttsx3 engine operations."""
        self.engine = pyttsx3.init()
        for text in iter(self._q.get, None):   # sentinel None shuts down
            if TTS_ENABLED:
                self.engine.say(text)
                self.engine.runAndWait()

    # enqueue text, return immediately
    def speak_async(self, text: str):
        if TTS_ENABLED:
            self._q.put(text)

    # interrupt current speech instantly
    def stop(self):
        if TTS_ENABLED and hasattr(self, "engine"):  # Check if engine has been initialized
            self.engine.stop()

    # clean shutdown (call in main finally:)
    def shutdown(self):
        if TTS_ENABLED:
            self._q.put(None)

tts = AsyncTTS()                              # Async text-to-speech engine

# HTTP session for reusing connections (improves performance by pooling connections)
# Set USE_HTTP_SESSION=0 in your .env to disable pooling if it causes issues.
USE_HTTP_SESSION = os.getenv("USE_HTTP_SESSION", "1") != "0"
session = requests.Session() if USE_HTTP_SESSION else requests

# Music bot configuration from environment
guild_id = os.getenv("GUILD_ID")             # Discord server ID
user_id = os.getenv("USER_ID")               # User's Discord ID
voice_channel_id = os.getenv("VOICE_CHANNEL_ID")  # Target voice channel
music_bot_base_url = os.getenv("MUSIC_BOT_URL")

# Add a check for music_bot_base_url
if music_bot_base_url is None:
    console_ui.print_error("ERROR: The MUSIC_BOT_URL environment variable is not set.")
    console_ui.print_error("Please ensure it is defined in your .env file (e.g., MUSIC_BOT_URL=http://localhost:3000/api/).")
    console_ui.print_error("Music bot commands will not function.")
    # Optionally, you could raise an exception here or set a flag to disable music commands
    # For now, it will print the error and continue, but API calls will fail.

# Configure and initialize shared audio input stream
RATE = 16_000                                # Audio sample rate in Hz (samples per second)
CHUNK = 512                                  # Number of audio frames per buffer (chunk size)
_pa = pyaudio.PyAudio()                      # Private PyAudio instance for managing audio resources
shared_stream = _pa.open(format=pyaudio.paInt16,  # 16-bit PCM audio format
                        channels=1,                 # Mono audio
                        rate=RATE,                  # Sample rate
                        input=True,                 # Specifies that this is an input stream
                        frames_per_buffer=CHUNK)    # Number of frames per buffer
# This shared_stream is used by both wake word detection and transcription modules.

def display_microphone_info():
    """Print information about the microphone Jarvis is using."""
    try:
        info = _pa.get_default_input_device_info()
        name = info.get("name", "Unknown")
        console_ui.print_info(f"Using microphone: {name}")
    except Exception as e:
        console_ui.print_warning(f"Could not determine microphone info: {e}")

def send_play_command(song_name: str):
    """
    Send request to music bot to play a specific song.

    Args:
        song_name: Name/query of the song to play

    Returns:
        dict: Response from the music bot API, or None on failure
    """
    url = f"{music_bot_base_url}play"
    payload = {
        "guildId": guild_id,                # Discord Server ID where the bot operates
        "userId": user_id,                  # Discord User ID of the person issuing the command
        "voiceChannelId": voice_channel_id,  # Discord Voice Channel ID to join/play in
        "options": {"query": song_name}      # Command-specific options, here the song query
    }
    try:
        return session.post(url, json=payload).json()
    except Exception as e:
        console_ui.print_error(f"Play request failed: {e}")
        return None

def send_command(command: str):
    """
    Send a control command to the music bot.

    Args:
        command: Command name (e.g., 'pause', 'resume', 'stop')

    Returns:
        dict: Response from the music bot API, or None on failure
    """
    url = f"{music_bot_base_url}{command}"
    payload = {
        "guildId": guild_id,                # Discord Server ID
        "userId": user_id,                  # Discord User ID
        "voiceChannelId": voice_channel_id,  # Discord Voice Channel ID
        "options": {}                       # General commands usually don't need specific options
    }
    try:
        return session.post(url, json=payload).json()
    except Exception as e:
        console_ui.print_error(f"Command request failed: {e}")
        return None

def listen_for_voice_commands():
    """
    Main voice command loop.
    
    Continuously listens for wake word, transcribes subsequent speech,
    interprets commands, and executes appropriate actions. Supports
    music playback control and self-termination commands.
    """
    while True:
        console_ui.print_command_prompt()
        # wait_for_wake_word now returns the pre-buffered audio
        pre_buffered_audio = wait_for_wake_word(shared_stream)
        
        # If pre_buffered_audio is empty, it might mean Porcupine isn't initialized
        # or an error occurred. We can choose to continue or handle it.
        # For now, we'll proceed, and transcribe.py will handle an empty buffer.
        if not pre_buffered_audio:
            console_ui.print_warning("Warning: No pre-buffered audio received. Proceeding without it.")
            # Optionally, you could 'continue' here to re-listen if this is critical

        tts.stop()   # interrupt any ongoing speech
        tts.speak_async("Yes?")  # Acknowledge wake word
        console_ui.print_jarvis_response("Yes?")
        
        transcript = ""
        # Pass the pre_buffered_audio to record_and_transcribe
        for partial in record_and_transcribe(shared_stream, initial_audio_buffer=pre_buffered_audio):
            # overwrite the current line with the growing sentence
            console_ui.print_transcription_feedback(partial)
            transcript = partial          # will end up holding the final yield
        console_ui.clear_line_then_print() # Clears the partial transcription line
        # Remove "Jarvis" if it's at the beginning of the transcript, case-insensitively,
        # and handle potential following comma/space.
        cleaned_transcript = transcript 
        words = transcript.split(None, 1) # Split into first word and the rest
        if words and words[0].lower().rstrip(',') == "jarvis":
            cleaned_transcript = words[1] if len(words) > 1 else ""
        
        cleaned_transcript = cleaned_transcript.strip() # Final strip for good measure

        # Check for 'cancel' command first
        if "cancel" in cleaned_transcript.lower():
            console_ui.print_info("User said 'cancel'. Aborting current command.")
            tts.speak_async("Cancelled.")
            console_ui.print_jarvis_response("Cancelled.")
            continue # Skip the rest of command processing and listen for wake word again

        console_ui.print_user_said(cleaned_transcript)


        # Command interpretation and execution
        # Use a lowercased version of the cleaned_transcript for command matching.
        command_text_for_matching = cleaned_transcript.lower()

        if ("now" in command_text_for_matching and "playing" in command_text_for_matching):
            tts.speak_async("Now playing.")
            console_ui.print_jarvis_response("Now playing.")
            send_command("now-playing")
        elif "played" in command_text_for_matching:
            # Extract song name. Find the start of "played" in the lowercased command string.
            idx = command_text_for_matching.find("played")
            # Slice the original-casing 'cleaned_transcript' from after "played" to get the song name.
            # This preserves the original capitalization of the song title.
            song = cleaned_transcript[idx + len("played"):].strip()
            if song:
                tts.speak_async(f"Playing {song}")
                console_ui.print_jarvis_response(f"Playing {song}")
                send_play_command(song)
        elif "play" in command_text_for_matching:
            # Similar to "played", extract song name after "play".
            idx = command_text_for_matching.find("play")
            # Slice the original-casing 'cleaned_transcript' to preserve song title capitalization.
            song = cleaned_transcript[idx + len("play"):].strip()
            if song:
                tts.speak_async(f"Playing {song}")
                console_ui.print_jarvis_response(f"Playing {song}")
                send_play_command(song)
        # Basic playback controls
        elif "stop"   in command_text_for_matching: 
            tts.speak_async("Stopping.")
            console_ui.print_jarvis_response("Stopping.")
            send_command("stop")
        elif "pause"  in command_text_for_matching: 
            tts.speak_async("Pausing.")
            console_ui.print_jarvis_response("Pausing.")
            send_command("pause")
        elif "resume" in command_text_for_matching: 
            tts.speak_async("Resuming.")
            console_ui.print_jarvis_response("Resuming.")
            send_command("resume")
        elif "next"   in command_text_for_matching: 
            tts.speak_async("Skipping.")
            console_ui.print_jarvis_response("Skipping.")
            send_command("next")
        elif "clear"  in command_text_for_matching: 
            tts.speak_async("Clearing.")
            console_ui.print_jarvis_response("Clearing.")
            send_command("clear")
        # Exit commands
        elif ("kill" in command_text_for_matching and "self" in command_text_for_matching) or \
             ("self" in command_text_for_matching and "destruct" in command_text_for_matching):
            tts.speak_async("Goodbye.")
            console_ui.print_jarvis_response("Goodbye.")
            break
        else:
            if cleaned_transcript: # Only say "Huh?" if there was actual text after cleaning
                tts.speak_async("Huh?")
                console_ui.print_jarvis_response("Huh?")

def prompt_for_tts():
    """Ask the user whether text-to-speech should be disabled."""
    global TTS_ENABLED
    choice = console_ui.console.input(
        "[prompt_style]Disable text-to-speech? [y/N]: [/prompt_style]"
    ).strip().lower()
    if choice == "y":
        TTS_ENABLED = False
        tts.shutdown()
        console_ui.print_info("Text-to-speech disabled.")
    else:
        console_ui.print_info("Text-to-speech enabled.")

def prompt_for_silence_settings():
    """Prompts the user to adjust silence detection settings at startup."""
    console_ui.print_header("Silence Detection Settings (Optional)")
    console_ui.print_info(
        "Values are loaded from the VOSK_RMS_THRESHOLD and VOSK_SILENCE_DURATION_SECONDS variables in .env."
    )

    # RMS Threshold
    current_rms = get_rms_threshold()
    console_ui.print_info(
        f"Current RMS Threshold: {current_rms} (Default: 900)"
    )
    console_ui.print_info("Lower values are more sensitive to silence; higher values are less sensitive.")
    new_rms_str = console_ui.console.input(f"[prompt_style]Enter new RMS Threshold (e.g., 500-1500) or press Enter to keep [{current_rms}]: [/prompt_style]").strip()
    if new_rms_str:
        try:
            new_rms = int(new_rms_str)
            set_rms_threshold(new_rms)
        except ValueError:
            console_ui.print_warning(f"Invalid input: '{new_rms_str}'. RMS Threshold not changed.")

    # Silence Duration
    current_duration = get_silence_duration_seconds()
    console_ui.print_info(
        f"\nCurrent Silence Duration: {current_duration:.1f}s (Default: 1.2s)"
    )
    console_ui.print_info("Longer duration allows for more pauses; shorter duration is more responsive.")
    new_duration_str = console_ui.console.input(f"[prompt_style]Enter new Silence Duration in seconds (e.g., 0.8-2.5) or press Enter to keep [{current_duration:.1f}s]: [/prompt_style]").strip()
    if new_duration_str:
        try:
            new_duration = float(new_duration_str)
            set_silence_duration(new_duration)
        except ValueError:
            console_ui.print_warning(f"Invalid input: '{new_duration_str}'. Silence Duration not changed.")
    console_ui.print_header("Settings Applied")

def main():
    """
    Entry point: Initialize and run the voice assistant.
    
    Ensures proper cleanup of audio resources on exit.
    """
    try:
        console_ui.print_header("Jarvis Voice Assistant")
        display_microphone_info()
        prompt_for_tts()
        prompt_for_silence_settings() # Prompt user for silence settings before full initialization
        console_ui.print_status("Starting Jarvis...")
        # Start the main loop to listen for wake word and commands
        listen_for_voice_commands()
    finally:
        # This block ensures that resources are cleaned up regardless of how the try block exits
        console_ui.print_status("Shutting down Jarvis and cleaning up resources...")
        if 'shared_stream' in locals() and shared_stream.is_active():
            shared_stream.stop_stream()  # Stop the stream before closing
            shared_stream.close()        # Release the audio stream resource
        if '_pa' in locals():
            _pa.terminate()              # Terminate the PyAudio session
        if 'tts' in locals():
            tts.shutdown()               # Gracefully shut down the TTS worker thread
        console_ui.print_success("Cleanup complete. Goodbye!")

# Standard Python entry point: ensures main() is called only when the script is executed directly.
if __name__ == "__main__":
    main()