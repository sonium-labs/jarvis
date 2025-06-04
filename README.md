# Jarvis

## Overview
Jarvis is a script that will listen to your voice and send music bot commands to my Muse fork.

Rename `.env.example` to `.env` in the `jarvis` directory after you clone. The contents look like so:

```
PORCUPINE_KEY="<YOUR-KEY>"
GUILD_ID=<YOUR-GUILD-ID>
USER_ID=<YOUR-USER-ID>
VOICE_CHANNEL_ID=<VOICE_CHANNEL_ID>
SERVER_IP=<YOUR-SERVER-IP>
```

Get a Porcupine key from [here]([url](https://console.picovoice.ai/signup)), and put Discord in developer mode to right click on things to get the IDs.

## Setup
`pip install pynput pyaudio vosk pvporcupine pyttsx3 numpy`

Then a human has to type `/join` in the target channel so the bot knows where to go.

## Usage
`python jarvis.py`

Then say: _"Jarvis, play hamster dance"_ (should use your default audio input) and it will send the command! (Doesn't really tell you in that channel though, if we can write to a channel in a future update we're golden). Works with other common commands too:

| 🔤 Phrase              | 🛠️ Action Performed               | 📤 Command Sent                              |
| ---------------------- | ---------------------------------- | --------------------------------------------- |
| `"play [song name]"`   | Play a song by name                | `/play [song name]`                           |
| `"now playing"`        | Display current track              | `/now-playing`                                |
| `"pause"`              | Pause playback                     | `/pause`                                      |
| `"resume"`             | Resume paused playback             | `/resume`                                     |
| `"next"`               | Skip to the next song              | `/next`                                       |
| `"clear"`              | Clear the playlist or queue        | `/clear`                                      |
| `"stop"`               | Stop playback                      | `/stop`                                       |
