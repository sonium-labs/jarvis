from wake_word import wait_for_wake_word
from transcribe import record_and_transcribe
from pynput.keyboard import Controller, Key
from screeninfo import get_monitors
import pygetwindow
import time
import pyautogui

########### Configs ###########
monitor_number = 2 # 1 is Windows monitor 1, etc.
textbox_x_padding = 300
textbox_y_padding = 50
discord_switch_delay_sec = 0.5
###############################

keyboard = Controller()

def get_discord_input_coords():
    monitors = get_monitors()
    target_monitor = monitors[monitor_number - 1] # don't hate me just helping out the homies

    # target area: bottom right with padding
    x = target_monitor.x + target_monitor.width - textbox_x_padding
    y = target_monitor.y + target_monitor.height - textbox_y_padding

    return x, y

def click_text_input_field():
    original_x, original_y = pyautogui.position()

    x, y = get_discord_input_coords()
    pyautogui.moveTo(x, y, duration=0.01)
    pyautogui.click()

    pyautogui.moveTo(original_x, original_y, duration=0)

def type_like_macro(text, delay=0.03):
    for char in text:
        keyboard.type(char)
        time.sleep(delay)

def listen_for_voice_commands():
    while True:
        print("Say \"Jarvis\" to wake...")
        wait_for_wake_word()
        print("Wake word detected.")
        transcript = record_and_transcribe()
        print(f"You said: {transcript}")

        if ("now" in transcript and "playing" in transcript):
            print("Now playing command detected.")
            send_command("/now-playing")
        elif "played" in transcript:
            print("Play command detected.")
            song_name = transcript.replace("played", "", 1).strip()
            if song_name:
                send_play_command(song_name)
        elif "play" in transcript:
            print("Play command detected.")
            song_name = transcript.replace("play", "", 1).strip()
            if song_name:
                send_play_command(song_name)
        elif "stop" in transcript:
            print("Stop playback command detected.")
            send_command("/stop")
        elif "pause" in transcript:
            print("Pause playback command detected.")
            send_command("/pause")
        elif "resume" in transcript:
            print("Resume playback command detected.")
            send_command("/resume")
        elif "next" in transcript:
            print("Skip track command detected.")
            send_command("/next")
        elif "clear" in transcript:
            print("Clear queue command detected.")
            send_command("/clear")
        elif ("kill" in transcript and "self" in transcript) or ("self" in transcript and "destruct" in transcript):
            print("Kill command detected.")
            quit()
        else:
            print("No known command found.")

def focus_discord():
    try:
        windows = pygetwindow.getWindowsWithTitle("Discord")
        if not windows:
            print("Discord window not found.")
            return False

        window = windows[0]
        if window.isMinimized:
            window.restore()
            time.sleep(0.5)

        try:
            window.activate()
        except pygetwindow.PyGetWindowException:
            print("Couldn't activate window")
            return False

        time.sleep(discord_switch_delay_sec)
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