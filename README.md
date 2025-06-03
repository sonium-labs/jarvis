# Jarvis

## Overview
Jarvis is a hacky script that will listen to your voice and send music bot commands in a Discord window of your choosing.

Get a key from https://console.picovoice.ai/signup and dump it into a file called `.env` in this directory. The contents should look like so:

`PORCUPINE_KEY="<YOUR-KEY-HERE>"`

## Setup
`pip install pynput pygetwindow pyautogui screeninfo pyaudio vosk pvporcupine numpy`

Put Discord on your second monitor, justified to the right so the text box is on the lower-right (told you this was hacky).

## Usage
`python jarvis.py`

Then say: _"Jarvis, play hampster dance"_ and it will type /play [tab] hampster dance in your target window! Works with other common commands too:

| 🔤 Phrase              | 🛠️ Action Performed               | 📤 Command Sent                              |
| ---------------------- | ---------------------------------- | --------------------------------------------- |
| `"play [song name]"`   | Play a song by name                | `/play [song name]`                           |
| `"now playing"`        | Display current track              | `/now-playing`                                |
| `"pause"`              | Pause playback                     | `/pause`                                      |
| `"resume"`             | Resume paused playback             | `/resume`                                     |
| `"next"`               | Skip to the next song              | `/next`                                       |
| `"clear"`              | Clear the playlist or queue        | `/clear`                                      |
| `"stop"`               | Stop playback                      | `/stop`                                       |
