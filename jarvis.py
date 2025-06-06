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
import logging
from dotenv import load_dotenv

from transcribe import record_and_transcribe
from wake_word import wait_for_wake_word

# Initialize environment variables and global service objects
load_dotenv()                                 # Load configuration from .env file

# ─── async, interruptible text-to-speech ────────────────────────────────
class AsyncTTS:
    """Threaded pyttsx3 wrapper with .speak_async() and .stop()."""
    def __init__(self):
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)  # daemon=True allows main program to exit even if thread is running
        self._thread.start()

    def _worker(self):
        """Dedicated worker thread for pyttsx3 engine operations."""
        try:
            self.engine = pyttsx3.init()
        except ValueError:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty("voices")
            if voices:
                self.engine.setProperty("voice", voices[0].id)
            logging.warning("pyttsx3 init failed; using first available voice")
        for text in iter(self._q.get, None):   # sentinel None shuts down
            self.engine.say(text)
            self.engine.runAndWait()

    # enqueue text, return immediately
    def speak_async(self, text: str):
        self._q.put(text)

    # interrupt current speech instantly
    def stop(self):
        if hasattr(self, "engine"):  # Check if engine has been initialized
            self.engine.stop()

    # clean shutdown (call in main finally:)
    def shutdown(self):
        self._q.put(None)

tts = AsyncTTS()                              # Async text-to-speech engine

# HTTP session for reusing connections (improves performance by pooling connections)
session = requests.Session()

# Music bot configuration from environment
guild_id = os.getenv("GUILD_ID")             # Discord server ID
user_id = os.getenv("USER_ID")               # User's Discord ID
voice_channel_id = os.getenv("VOICE_CHANNEL_ID")  # Target voice channel
music_bot_base_url = os.getenv("MUSIC_BOT_URL")

# Add a check for music_bot_base_url
if music_bot_base_url is None:
    print("\nERROR: The MUSIC_BOT_URL environment variable is not set.")
    print("Please ensure it is defined in your .env file (e.g., MUSIC_BOT_URL=http://localhost:3000/api/).")
    print("Music bot commands will not function.\n")
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
        print(f"Play request failed: {e}")
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
        print(f"Command request failed: {e}")
        return None

def listen_for_voice_commands():
    """
    Main voice command loop.
    
    Continuously listens for wake word, transcribes subsequent speech,
    interprets commands, and executes appropriate actions. Supports
    music playback control and self-termination commands.
    """
    while True:
        print('Say "Jarvis" to wake...')
        # wait_for_wake_word now returns the pre-buffered audio
        pre_buffered_audio = wait_for_wake_word(shared_stream)
        
        # If pre_buffered_audio is empty, it might mean Porcupine isn't initialized
        # or an error occurred. We can choose to continue or handle it.
        # For now, we'll proceed, and transcribe.py will handle an empty buffer.
        if not pre_buffered_audio:
            print("Warning: No pre-buffered audio received. Proceeding without it.")
            # Optionally, you could 'continue' here to re-listen if this is critical

        tts.stop()   # interrupt any ongoing speech
        print("Wake word detected.")
        tts.speak_async("Yes?")  # Acknowledge wake word
        
        transcript = ""
        # Pass the pre_buffered_audio to record_and_transcribe
        for partial in record_and_transcribe(shared_stream, initial_audio_buffer=pre_buffered_audio):
            # overwrite the current line with the growing sentence
            print('\r' + partial + ' ' * 20, end='', flush=True)
            transcript = partial          # will end up holding the final yield
        print()                           # newline after the overwrite loop
        # Remove "Jarvis" if it's at the beginning of the transcript, case-insensitively,
        # and handle potential following comma/space.
        cleaned_transcript = transcript 
        words = transcript.split(None, 1) # Split into first word and the rest
        if words and words[0].lower().rstrip(',') == "jarvis":
            cleaned_transcript = words[1] if len(words) > 1 else ""
        
        cleaned_transcript = cleaned_transcript.strip() # Final strip for good measure

        # Check for 'cancel' command first
        if "cancel" in cleaned_transcript.lower():
            print("User said 'cancel'. Aborting current command.")
            tts.speak_async("Cancelled.")
            continue # Skip the rest of command processing and listen for wake word again

        print(f"You said: {cleaned_transcript}")


        # Command interpretation and execution
        # Use a lowercased version of the cleaned_transcript for command matching.
        command_text_for_matching = cleaned_transcript.lower()

        if ("now" in command_text_for_matching and "playing" in command_text_for_matching):
            tts.speak_async("Now playing.")
            send_command("now-playing")
        elif "played" in command_text_for_matching:
            # Extract song name. Find the start of "played" in the lowercased command string.
            idx = command_text_for_matching.find("played")
            # Slice the original-casing 'cleaned_transcript' from after "played" to get the song name.
            # This preserves the original capitalization of the song title.
            song = cleaned_transcript[idx + len("played"):].strip()
            if song:
                tts.speak_async(f"Playing {song}")
                send_play_command(song)
        elif "play" in command_text_for_matching:
            # Similar to "played", extract song name after "play".
            idx = command_text_for_matching.find("play")
            # Slice the original-casing 'cleaned_transcript' to preserve song title capitalization.
            song = cleaned_transcript[idx + len("play"):].strip()
            if song:
                tts.speak_async(f"Playing {song}")
                send_play_command(song)
        # Basic playback controls
        elif "stop"   in command_text_for_matching: tts.speak_async("Stopping.");  send_command("stop")
        elif "pause"  in command_text_for_matching: tts.speak_async("Pausing.");   send_command("pause")
        elif "resume" in command_text_for_matching: tts.speak_async("Resuming.");  send_command("resume")
        elif "next"   in command_text_for_matching: tts.speak_async("Skipping.");  send_command("next")
        elif "clear"  in command_text_for_matching: tts.speak_async("Clearing.");  send_command("clear")
        # Exit commands
        elif ("kill" in command_text_for_matching and "self" in command_text_for_matching) or \
             ("self" in command_text_for_matching and "destruct" in command_text_for_matching):
            tts.speak_async("Goodbye.")
            break
        else:
            if cleaned_transcript: # Only say "Huh?" if there was actual text after cleaning
                tts.speak_async("Huh?")

def main():
    """
    Entry point: Initialize and run the voice assistant.
    
    Ensures proper cleanup of audio resources on exit.
    """
    try:
        print("Starting Jarvis...")
        # Start the main loop to listen for wake word and commands
        listen_for_voice_commands()
    finally:
        # This block ensures that resources are cleaned up regardless of how the try block exits
        print("\nShutting down Jarvis and cleaning up resources...")
        if 'shared_stream' in locals() and shared_stream.is_active():
            shared_stream.stop_stream()  # Stop the stream before closing
            shared_stream.close()        # Release the audio stream resource
        if '_pa' in locals():
            _pa.terminate()              # Terminate the PyAudio session
        if 'tts' in locals():
            tts.shutdown()               # Gracefully shut down the TTS worker thread
        print("Cleanup complete. Goodbye!")

# Standard Python entry point: ensures main() is called only when the script is executed directly.
if __name__ == "__main__":
    main()