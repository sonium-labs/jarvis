# Jarvis
![image](https://github.com/user-attachments/assets/66ffb78c-fc72-410e-a3e4-7a785a508364)


## Overview
Jarvis is a small voice control script that listens for commands and sends them
to a remote Discord music bot using HTTP requests.

Get a Porcupine key from [here](https://console.picovoice.ai/signup) and create a new file
named `.env` in this directory containing your Porcupine and Discord details:

```
PORCUPINE_KEY="<YOUR-PORCUPINE-KEY>"
GUILD_ID="<DISCORD-GUILD-ID>"
USER_ID="<YOUR-DISCORD-USER-ID>"
VOICE_CHANNEL_ID="<TARGET-VOICE-CHANNEL-ID>"
MUSIC_BOT_URL="<YOUR-MUSIC-BOT-URL>"
```

## Setup
1. Install the required Python packages:

```
pip install pyaudio vosk pvporcupine numpy pyttsx3 requests python-dotenv
```

2. Download the Vosk English model from
   [here](https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip) and
   extract its contents into a new directory called `model`.


## Usage
`python jarvis.py`

Then say: _"Jarvis, play hamster dance"_ (using your default microphone) and Jarvis
will instruct the music bot to play it. Works with other common commands too:

| 🔤 Phrase              | 🛠️ Action Performed               | 📤 Command Sent                              |
| ---------------------- | ---------------------------------- | --------------------------------------------- |
| `"play [song name]"`   | Play a song by name                | `/play [song name]`                           |
| `"pause"`              | Pause playback                     | `/pause`                                      |
| `"resume"`             | Resume paused playback             | `/resume`                                     |
| `"next"`               | Skip to the next song              | `/next`                                       |
| `"clear"`              | Clear the playlist or queue        | `/clear`                                      |
| `"stop"`               | Stop playback                      | `/stop`                                       |
| `"now playing"`        | Display current track              | `/now-playing`                                |
