import os
import sys

# suppress stderr output (from vosk) (and also accidentally Python errors oops)
devnull = os.open(os.devnull, os.O_WRONLY)
os.dup2(devnull, sys.stderr.fileno())

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
