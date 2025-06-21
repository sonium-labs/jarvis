import pyttsx3
import pyttsx3.drivers.sapi5 as sapi5
import weakref
import comtypes.client

# --- Monkey-patch to bypass broken voice init ---
def patched_init(self, proxy):
    self._tts = comtypes.client.CreateObject('SAPI.SpVoice')
    self._tts.EventInterests = 33790
    self._event_sink = sapi5.SAPI5DriverEventSink()
    self._event_sink.setDriver(weakref.proxy(self))
    self._advise = comtypes.client.GetEvents(self._tts, self._event_sink)
    self._proxy = proxy
    self._looping = False
    self._speaking = False
    self._stopping = False
    self._current_text = ''
    self._rateWpm = 200
    # 🚫 Do not set voice here — we will do it explicitly later

sapi5.SAPI5Driver.__init__ = patched_init

# --- Use pyttsx3 safely ---
engine = pyttsx3.init()
voices = engine.getProperty("voices")

# Print available voices
print("Available voices:")
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name} - {voice.id}")

# Pick Zira safely
zira = next((v for v in voices if "zira" in v.name.lower()), None)

if zira:
    engine.setProperty("voice", zira.id)
    engine.say("Hello from pyttsx3 using Zira!")
    engine.runAndWait()
else:
    raise RuntimeError("Zira not found!")
