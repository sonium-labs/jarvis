import os
import sys

class SuppressCStderr:
    def __enter__(self):
        self.stderr_fd = sys.stderr.fileno()

        # Save a copy of the original stderr
        self.saved_stderr_fd = os.dup(self.stderr_fd)

        # Open /dev/null and redirect stderr to it
        self.devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self.devnull_fd, self.stderr_fd)

        return self  # <--- needed for context managers

    def __exit__(self, exc_type, exc_value, traceback):
        # Restore original stderr
        os.dup2(self.saved_stderr_fd, self.stderr_fd)
        os.close(self.devnull_fd)
        os.close(self.saved_stderr_fd)

from vosk import Model, KaldiRecognizer
import pyaudio
import wave
import json

def record_and_transcribe():
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 4
    WAVE_OUTPUT_FILENAME = "temp.wav"

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Done recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print("Transcribing...")

    with SuppressCStderr():
        model = Model("model")
        rec = KaldiRecognizer(model, RATE)

        wf = wave.open(WAVE_OUTPUT_FILENAME, "rb")
        results = []

        while True:
            data = wf.readframes(CHUNK)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                results.append(result.get("text", ""))

    final_text = " ".join(results).strip()
    return final_text

if __name__ == "__main__":
    text = record_and_transcribe()
    print(f"You said: {text}")
