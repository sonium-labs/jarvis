from wake_word import wait_for_wake_word
from transcribe import record_and_transcribe
from pynput.keyboard import Controller, Key
from screeninfo import get_monitors
import pygetwindow
import time
import pyautogui

######### Configs #########
textbox_x_padding = 300
textbox_y_padding = 50
discord_switch_delay = 0.4
###########################

keyboard = Controller()

def get_discord_input_coords():
    monitors = get_monitors()
    if len(monitors) < 2:
        raise RuntimeError("Second monitor not found.")

    second = monitors[1]

    # target area: bottom right with padding
    x = second.x + second.width - textbox_x_padding
    y = second.y + second.height - textbox_y_padding

    return x, y

def click_text_input_field():
    original_x, original_y = pyautogui.position()

    x, y = get_discord_input_coords()
    pyautogui.moveTo(x, y, duration=0)
    pyautogui.click()

    pyautogui.moveTo(original_x, original_y, duration=0)

def type_like_macro(text, delay=0.03):
    for char in text:
        keyboard.type(char)
        time.sleep(delay)

def listen_for_voice_commands():
    while True:
        print("Waiting for wake word...")
        wait_for_wake_word()
        print("Wake word detected.")
        transcript = record_and_transcribe()
        print(f"You said: {transcript}")

        if "now playing" in transcript:
            print("Clear command detected.")
            send_command("/now-playing")
        if "play" in transcript:
            song_name = transcript.replace("play", "").strip()
            if song_name:
                send_play_command(song_name)
        elif "played" in transcript:
            song_name = transcript.replace("played", "").strip()
            if song_name:
                send_play_command(song_name)
        elif "stop" in transcript:
            print("Stopping playback command detected.")
            send_command("/stop")
        elif "pause" in transcript:
            print("Pause playback command detected.")
            send_command("/pause")
        elif "resume" in transcript:
            print("Resume playback command detected.")
            send_command("/resume")
        elif "next" in transcript:
            print("Skip playback command detected.")
            send_command("/next")
        elif "clear" in transcript:
            print("Clear command detected.")
            send_command("/clear")
        else:
            print("No known command found.")

def focus_discord():
    try:
        windows = pygetwindow.getWindowsWithTitle("Discord")
        if not windows:
            print("Discord window not found.")
            return False

        window = windows[0]  # Use the first match
        if window.isMinimized:
            window.restore()
            time.sleep(0.5)

        try:
            window.activate()
        except pygetwindow.PyGetWindowException:
            print("Couldn't activate window")
            return False

        time.sleep(discord_switch_delay)
        return True

    except Exception as e:
        print(f"Error focusing Discord: {e}")
        return False

def send_play_command(song_name: str):
    if not focus_discord():
        return

    delay = 0.05
    click_text_input_field()

    type_like_macro("/play", delay=0.01)

    keyboard.press(Key.tab)
    keyboard.release(Key.tab)

    type_like_macro(f"{song_name}", delay=0.01)

    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(delay)

    pyautogui.hotkey('alt', 'tab')
    time.sleep(0.5) # wait for the original window to focus

def send_command(command: str):
    if not focus_discord():
        return

    delay = 0.05
    click_text_input_field()

    type_like_macro(f"{command}", delay=0.01)

    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(delay)

    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(delay)

    pyautogui.hotkey('alt', 'tab')
    time.sleep(0.5) # wait for the original window to focus

def main():
    print("Starting Jarvis...")

    # for some reason you need to click the window first
    # to ensure Discord window can be activated on first run???
    # not even a manual click works...

    click_text_input_field()

    print("Starting voice command listener...")
    listen_for_voice_commands()

if __name__ == "__main__":
    main()