# Jarvis

## Overview
Jarvis is a hacky script that will listen to your voice and send music bot commands in a Discord window of your choosing.

Get a key from [here]([url](https://console.picovoice.ai/signup)) and create a new file called `.env` in the `jarvis` directory after you clone, with contents like so:

`PORCUPINE_KEY="<YOUR-KEY-HERE>"`

## Setup
`pip install pynput pygetwindow pyautogui screeninfo pyaudio vosk pvporcupine numpy`

By default, put Discord on your second monitor, justified to the right so the text box is on the lower-right (told you this was hacky). I use this bot in a voice channel so the textbox is in the bottom right by default, but if your text box is somewhere else (or on a different monitor), update the config section at the top of `jarvis.py`.

## Usage
`python jarvis.py`

Then say: _"Jarvis, play hampster dance"_ (should use your default audio input) and it will type `/play [tab] hampster dance` in your Discord window! Works with other common commands too:

| 🔤 Phrase              | 🛠️ Action Performed               | 📤 Command Sent                              |
| ---------------------- | ---------------------------------- | --------------------------------------------- |
| `"play [song name]"`   | Play a song by name                | `/play [song name]`                           |
| `"now playing"`        | Display current track              | `/now-playing`                                |
| `"pause"`              | Pause playback                     | `/pause`                                      |
| `"resume"`             | Resume paused playback             | `/resume`                                     |
| `"next"`               | Skip to the next song              | `/next`                                       |
| `"clear"`              | Clear the playlist or queue        | `/clear`                                      |
| `"stop"`               | Stop playback                      | `/stop`                                       |
