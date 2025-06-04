from wake_word import wait_for_wake_word
from transcribe import record_and_transcribe
from pynput.keyboard import Controller
import os
from dotenv import load_dotenv
import requests
import pyttsx3

# Load environment variables from .env file
load_dotenv()

keyboard = Controller()

guild_id = os.getenv("GUILD_ID")
user_id = os.getenv("USER_ID")
voice_channel_id = os.getenv("VOICE_CHANNEL_ID")
server_ip = os.getenv("SERVER_IP")

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

def speak(text: str):
    tts_engine.say(text)
    tts_engine.runAndWait()

def listen_for_voice_commands():
    while True:
        print("Say \"Jarvis\" to wake...")
        wait_for_wake_word()
        print("Wake word detected.")
        transcript = record_and_transcribe()
        print(f"You said: {transcript}")

        if ("now" in transcript and "playing" in transcript):
            print("Now playing command detected.")
            speak("Now playing.")
            send_command("now-playing")
        elif "played" in transcript:
            print("Play command detected.")
            song_name = transcript.replace("played", "", 1).strip()
            if song_name:
                speak(f"Playing {song_name}")
                send_play_command(song_name)
        elif "play" in transcript:
            print("Play command detected.")
            song_name = transcript.replace("play", "", 1).strip()
            if song_name:
                speak(f"Playing {song_name}")
                send_play_command(song_name)
        elif "stop" in transcript:
            print("Stop playback command detected.")
            speak("Stopping playback.")
            send_command("stop")
        elif "pause" in transcript:
            print("Pause playback command detected.")
            speak("Pausing playback.")
            send_command("pause")
        elif "resume" in transcript:
            print("Resume playback command detected.")
            speak("Resuming playback.")
            send_command("resume")
        elif "next" in transcript:
            print("Skip track command detected.")
            speak("Skipping track.")
            send_command("next")
        elif "clear" in transcript:
            print("Clear queue command detected.")
            speak("Clearing queue.")
            send_command("clear")
        elif ("kill" in transcript and "self" in transcript) or ("self" in transcript and "destruct" in transcript):
            print("Kill command detected.")
            speak("Goodbye.")
            quit()
        else:
            print("No known command found.")
            speak("Sorry, I didn't understand that command.")

def send_play_command(song_name: str):
    url = f"{server_ip}/command/play"
    payload = {
        "guildId": guild_id,
        "userId": user_id,
        "voiceChannelId": voice_channel_id,
        "options": {"query": song_name}
    }
    response = requests.post(url, json=payload)
    try:
        return response.json()
    except Exception:
        print("Non-JSON response:", response.status_code, response.text)
        return None

def send_command(command: str):
    url = f"{server_ip}/command/{command}"
    payload = {
        "guildId": guild_id,
        "userId": user_id,
        "voiceChannelId": voice_channel_id,
        "options": {}
    }
    response = requests.post(url, json=payload)
    try:
        return response.json()
    except Exception:
        print("Non-JSON response:", response.status_code, response.text)
        return None

def main():
    print("Starting Jarvis...")

    # for some reason you need to click the window first
    # to ensure Discord window can be activated on first run???
    # not even a manual click works...

    print("Starting voice command listener...")
    listen_for_voice_commands()

if __name__ == "__main__":
    main()