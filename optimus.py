# Optimus - your personal voice assistant
# Run visible:  python assistant.py      Run hidden:  pythonw assistant.py
import os
import sys
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# When started without a console window (pythonw), write messages to a file
if sys.stdout is None:
    _log = open(os.path.join(BASE_DIR, "optimus.log"), "a",
                encoding="utf-8", buffering=1)
    sys.stdout = _log
    sys.stderr = _log

# Stop black windows from flashing when we call PowerShell
_real_run = subprocess.run


def _quiet_run(*args, **kwargs):
    kwargs.setdefault("creationflags", 0x08000000)
    return _real_run(*args, **kwargs)


subprocess.run = _quiet_run

# Sharper subtitles and correct screenshots on scaled displays
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import re
import json
import queue
import random
import difflib
import threading
import webbrowser
import collections
import socket
import math
import shutil
import html as html_lib
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import tkinter as tk
from datetime import datetime, timedelta

import numpy as np
import psutil
import pyttsx3
import sounddevice as sd

try:
    from rapidfuzz import process as fuzz_process, fuzz
except Exception:
    fuzz_process = None
    fuzz = None


def add_cuda_paths():
    """Let the speech engine find the NVIDIA libraries installed by pip."""
    base = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
    for sub in ("cublas", "cudnn"):
        folder = os.path.join(base, sub, "bin")
        if os.path.isdir(folder):
            try:
                os.add_dll_directory(folder)
            except Exception:
                pass
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")


add_cuda_paths()
from faster_whisper import WhisperModel  # noqa: E402

# ===================== SETTINGS YOU CAN CHANGE =====================
USER_NAME = "sir"             # what Optimus calls you
OLLAMA_MODEL = "llama3.2"     # the AI brain
VOICE = "bm_george"           # also try: bm_lewis, bm_daniel, bm_fable
VOICE_SPEED = 0.95            # lower = slower
WHISPER_MODEL = "small.en"    # "base.en" is faster, "medium.en" is smarter
USE_GPU = True                # uses your NVIDIA graphics card if it works
FOLLOWUP_SECONDS = 10         # keeps listening this long after replying
HOME_CITY = ""                # e.g. "Chennai". Empty = guess from internet
NEWS_REGION = "hl=en-IN&gl=IN&ceid=IN:en"   # news edition (India)
MIC_THRESHOLD = None          # None = automatic. Lower number = more sensitive
BRAIN_KEEP_ALIVE = "2h"       # how long the offline AI stays loaded
ONLINE_MODEL = "claude-haiku-5-5"   # only used if api_key.txt exists
ONLINE_WEB_SEARCH = True      # lets the online brain search the web
VOICE_STYLE = "friendly"      # "friendly" (female), "jarvis" (male butler) or "overlord" (deep metallic villain)
VOICE_LOCK = True             # only answer to YOUR voice (say: learn my voice)
VOICE_LOCK_THRESHOLD = 0.45   # higher = stricter, lower = more forgiving
PTT_KEY = "rightctrl"         # hold to talk, tap to stop speech. "" turns it off
HEADPHONES_MODE = False       # True lets you interrupt it by speaking (headphones only)
BATTERY_SAVER_PERCENT = 20    # below this (unplugged) it listens only while you hold the key
WAKE_MODEL = "base.en"        # quick model that only listens for the wake word
SPEECH_LANGUAGE = "en"        # None = auto-detect (also set WHISPER_MODEL = "small")
VISION_MODEL = "gemma3:4b"    # the offline model that can see your screen
AUTO_BRIEFING = False         # morning briefing the first time you start each day
SHOW_ORB = True               # glowing orb in the bottom-right corner
FOCUS_MINUTES = 25
BREAK_MINUTES = 5
DISTRACTION_APPS = ["whatsapp", "discord", "instagram", "steam"]
GAMING_CLOSE_APPS = ["chrome", "edge", "onedrive", "teams"]
GAMING_APP = "steam"
ORB_STYLE = "logo"            # "logo" (your orb_logo.png), "reactor", "hud" or "pulse"
ORB_SIZE = 170                # orb size in pixels (also: mouse wheel over the orb)
ORB_IMAGE = "orb_logo.png"    # your own logo for the "image" style
END_SILENCE = 1.1             # seconds of quiet that end your sentence (higher = fewer cut-offs)
MIC_DEVICE_NAME = ""          # part of your microphone's name, e.g. "Headset". Empty = default
SUBTITLE_FONT = "Bahnschrift"
SUBTITLE_SIZE = 20
SUBTITLE_COLOR = "#8fefff"
# ===================================================================

WAKE_WORD = "optimus"
SAMPLE_RATE = 16000
HOME = os.path.expanduser("~")
# The full-quality voice sounds smoother than the small int8 one. If you
# download kokoro-v1.0.onnx into this folder it is used automatically.
MODEL_PATH = os.path.join(BASE_DIR, "kokoro-v1.0.onnx")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(BASE_DIR, "kokoro-v1.0.int8.onnx")
VOICES_PATH = os.path.join(BASE_DIR, "voices-v1.0.bin")
CACHE_FILE = os.path.join(BASE_DIR, "index_cache.json")
ALARMS_FILE = os.path.join(BASE_DIR, "alarms.json")
SHOTS_FILE = os.path.join(BASE_DIR, "screenshots.json")
GPU_FLAG = os.path.join(BASE_DIR, "gpu_loading.flag")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
KEY_FILE = os.path.join(BASE_DIR, "api_key.txt")
SPEAKER_MODEL_PATH = os.path.join(BASE_DIR, "speaker_model.onnx")
VOICEPRINT_FILE = os.path.join(BASE_DIR, "voiceprint.npy")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
TODO_FILE = os.path.join(BASE_DIR, "todo.json")
NOTES_FILE = os.path.join(BASE_DIR, "notes.txt")
HISTORY_LOG = os.path.join(BASE_DIR, "history_log.txt")
VOCAB_FILE = os.path.join(BASE_DIR, "vocabulary.txt")
TELEGRAM_TOKEN_FILE = os.path.join(BASE_DIR, "telegram_token.txt")
TELEGRAM_SECRET_FILE = os.path.join(BASE_DIR, "telegram_secret.txt")
SHOT_DIR = os.path.join(HOME, "Pictures", "Optimus Screenshots")
WIN_SHOT_DIR = os.path.join(HOME, "Pictures", "Screenshots")
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

OPEN_VERBS = {"open", "launch"}
CLOSE_VERBS = {"close", "quit"}
FILLERS = {"please", "can", "you", "could", "would", "the", "my",
           "app", "application", "program", "now", "me", "hey", "hi",
           "hello", "ok", "okay", "so"}
PROTECTED = {"python", "pythonw", "cmd", "powershell", "pwsh",
             "windowsterminal", "conhost", "explorer"}
SKIP_FOLDERS = {"appdata", "node_modules", "venv", "site-packages",
                "__pycache__", "windows", "program files",
                "program files (x86)", "programdata", "$recycle.bin",
                "system volume information"}
MAX_DEPTH = 3
MAX_INDEX = 200000
# Names only. Whisper copies the style of this prompt, so it must never contain
# whole commands (it used to, and that made it "hear" commands you never said).
PROMPT = "Optimus, ChatGPT, WhatsApp, YouTube, Spotify."
MIN_CONFIDENCE = -1.2         # recognised speech scoring below this is ignored
HALLUCINATIONS = {"you", "thanks for watching", "thank you for watching",
                  "the end", "uh", "um", "hmm", "oh", "so", "subscribe",
                  "please subscribe", "see you next time",
                  "see you in the next video", "i ll see you in the next video",
                  "thank you for listening", "thanks for listening",
                  "like and subscribe", "bye bye", "mm", "mhm", "ah"}
SOCIAL_PHRASES = {"thank you", "thanks", "thank you very much",
                  "thank you so much", "thanks a lot", "thank you sir",
                  "thanks optimus", "thank you optimus", "bye", "goodbye",
                  "cheers"}
last_spoken_at = {"t": 0.0}

PERSONA = (
    "You are Optimus, the user's personal AI companion on their laptop, "
    "in the spirit of JARVIS from Iron Man: calm, quick-witted and loyal. "
    "Talk like a real person, not a robot: use contractions, natural "
    "reactions and short sentences, and keep replies to one to three "
    "sentences unless asked for more. "
    "You have a dry, sarcastic sense of humour and you know internet slang "
    "and memes, Indian and global, so you can banter, riff on jokes and "
    "drop a meme reference when it fits. "
    "Notice sarcasm and irony in what the user says and answer in kind, "
    "playfully and never cruelly. "
    "If the user sounds stressed, sad or unwell, drop the jokes and be "
    "kind and supportive. "
    "Sound like a friendly person chatting, not a customer-service script: "
    "open with a quick natural reaction when it fits (like 'Sure', "
    "'Alright', 'Oh nice', 'Hmm'), vary your sentence length, and avoid "
    "stiff phrases such as 'certainly', 'I am unable to' or 'as an AI'. "
    "Be honest: if you do not know something or need live information you "
    "do not have, say so instead of guessing. "
    "Everything you write is spoken aloud, so never use lists, markdown, "
    "emojis or stage directions. "
    "Call the user " + USER_NAME + " now and then, not in every sentence."
)
RESEARCH_NOTE = (
    "Fresh web sources gathered just now are below. Use them to answer, "
    "prefer the newest, and mention briefly when something comes from "
    "recent news. If they do not cover the question, say so honestly. "
    "Never read out links or URLs."
)
ACKS = ["One moment, {n}.", "Let me check that.", "On it, {n}.",
        "Give me a second.", "Sure thing.", "Alright, let me take a look.",
        "Hang on a sec.", "Okay, checking now."]
WEATHER_TRIGGERS = ("weather", "forecast", "rain", "raining", "umbrella",
                    "temperature")
CITY_RE = (r"^(?:set |change )?(?:my )?(?:city|location|town|home)"
           r"(?: is| to| as)\s+(.+)$")
RESEARCH_RES = [
    r"^(?:browse|search|research|look up|lookup|find out|google)"
    r"(?: the web| online| the internet)?(?: about| for| on)?\s+(.+)$",
    r"^(?:tell me|let me know|explain to me)(?: more)? about\s+(.+)$",
    r"^i (?:want to|wanna) know (?:about )?(.+)$",
    r"^what(?: is| s|s) (?:happening|going on)(?: with| in| on| at)\s+(.+)$",
    r"^what(?: is| s|s) the latest(?: news)?(?: on| about| with)\s+(.+)$",
    r"^(?:latest|news)(?: news)?(?: on| about)\s+(.+)$",
    r"^what happened(?: to| with| in| at)\s+(.+)$",
]

FAREWELLS_DAY = [
    "Very good, {n}. I'll be right here whenever you need me.",
    "Of course, {n}. Do take care, and remember to drink some water.",
    "Until next time, {n}. It's always a pleasure.",
    "Off you go, {n}. I'll keep everything running while you're away.",
]
FAREWELLS_NIGHT = [
    "Good night, {n}. Do get some proper rest. I'll be here in the morning.",
    "Sleep well, {n}. Tomorrow is another good day to build something great.",
    "Rest up, {n}. You've earned it. Good night.",
]
END_EXACT = {"stop", "stop it", "stop talking", "stop listening",
             "that will be all"}
END_PHRASES = ["goodbye", "good bye", "bye", "bye bye", "see you",
               "see you later", "see you soon", "see ya", "catch you later",
               "talk to you later", "talk later", "good night",
               "that is all", "that s all", "thats all", "i am done",
               "i m done", "take care", "go to sleep"]
SHUTDOWN_PHRASES = ["shut down", "power off", "quit completely",
                    "exit completely"]

SPECIAL_FOLDERS = {
    "downloads": "shell:Downloads",
    "documents": "shell:Personal",
    "desktop": "shell:Desktop",
    "pictures": "shell:My Pictures",
    "music": "shell:My Music",
    "videos": "shell:My Video",
    "thispc": "shell:MyComputerFolder",
    "computer": "shell:MyComputerFolder",
    "recyclebin": "shell:RecycleBinFolder",
}
for _k in list(SPECIAL_FOLDERS):
    if _k.endswith("s"):
        SPECIAL_FOLDERS[_k[:-1]] = SPECIAL_FOLDERS[_k]

WEBSITES = {
    "browser": "https://www.google.com",
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
}
LETTERS = {"c": "c", "see": "c", "sea": "c", "d": "d", "dee": "d",
           "e": "e", "f": "f", "g": "g"}
NEWS_TOPICS = {
    "world": "WORLD", "india": "NATION", "national": "NATION",
    "business": "BUSINESS", "technology": "TECHNOLOGY",
    "tech": "TECHNOLOGY", "sports": "SPORTS", "sport": "SPORTS",
    "science": "SCIENCE", "health": "HEALTH",
    "entertainment": "ENTERTAINMENT",
}
WEATHER_WORDS = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy", 51: "drizzly", 53: "drizzly", 55: "drizzly",
    56: "freezing drizzle", 57: "freezing drizzle", 61: "lightly raining",
    63: "raining", 65: "raining heavily", 66: "freezing rain",
    67: "freezing rain", 71: "lightly snowing", 73: "snowing",
    75: "snowing heavily", 77: "snowing", 80: "showery", 81: "showery",
    82: "showery with heavy rain", 85: "snowy", 86: "snowy",
    95: "stormy", 96: "stormy with hail", 99: "stormy with hail",
}
VK = {"mute": 0xAD, "down": 0xAE, "up": 0xAF, "next": 0xB0,
      "prev": 0xB1, "stop": 0xB2, "playpause": 0xB3}
MEDIA_NOUNS = {"music", "song", "songs", "track", "tracks", "media",
               "playback", "it", "this", "that", "video", "audio", "one",
               "playing"}
NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60,
                "hour": 3600, "hr": 3600}
DURATION_RE = (r"(?:\b(?:in|after|for)\s+)?\b(?:\d+(?:\.\d+)?|an|a)\s*"
               r"(?:seconds?|secs?|minutes?|mins?|hours?|hrs?)\b")
CLOCK_RE = r"\b(?:at|for|by)\s+(\d{1,2})(?: (\d{2}))?\s*(a m|p m|am|pm)?\b"

# voice packs: name -> (voice id, accent, speed, effect, label, description)
VOICE_PACKS = {
    "jarvis": (VOICE, "en-gb", VOICE_SPEED, "", "Jarvis", "calm British butler"),
    "friendly": ("af_heart", "en-us", 1.0, "", "Friendly", "warm and bright"),
    "overlord": ("am_onyx", "en-us", 1.05, "overlord", "Overlord",
                 "deep, metallic villain"),
    "commander": ("am_michael", "en-us", 0.98, "", "Commander",
                  "steady and confident"),
    "sage": ("bm_fable", "en-gb", 0.95, "", "Sage", "thoughtful storyteller"),
    "agent": ("bm_lewis", "en-gb", 1.0, "", "Agent", "crisp British agent"),
    "cadet": ("am_puck", "en-us", 1.05, "", "Cadet", "quick and playful"),
    "nova": ("af_nova", "en-us", 1.0, "", "Nova", "clear and energetic"),
    "aurora": ("af_aoede", "en-us", 0.97, "", "Aurora", "soft and calm"),
    "sky": ("af_sky", "en-us", 1.02, "", "Sky", "light and airy"),
    "guardian": ("am_adam", "en-us", 0.95, "", "Guardian", "grounded, protective"),
    "lady": ("bf_emma", "en-gb", 0.98, "", "Lady", "polished British"),
    "spark": ("af_bella", "en-us", 1.05, "", "Spark", "cheerful and fast"),
    "droid": ("am_echo", "en-us", 1.0, "droid", "Droid", "robotic sidekick"),
    "radio": ("am_eric", "en-us", 1.0, "radio", "Radio", "crackly comms channel"),
    "titan": ("am_fenrir", "en-us", 0.92, "deep", "Titan", "very deep and heavy"),
}
VOICE_STYLES = {k: v[:3] for k, v in VOICE_PACKS.items()}
MODES = {
    "normal": "",
    "serious": "Right now be professional and concise. No jokes or sarcasm.",
    "sarcastic": ("Right now turn the sarcasm up: be extra witty and roast "
                  "gently, playful but never cruel."),
    "friendly": ("Right now be warm, encouraging and gentle, like a "
                 "supportive friend. No sarcasm."),
    "study": ("Right now act like a patient tutor: explain step by step in "
              "simple words, give one quick example, and finish with a short "
              "check question. Up to five short sentences."),
}
ENROLL_PROMPTS = [
    "The quick brown fox jumps over the lazy dog.",
    "Optimus, open my downloads folder and tell me the weather.",
    "I am training my assistant to recognise only my voice.",
    "Please set a timer for ten minutes and play some music.",
    "Good morning, what is the latest news today?",
    "Code red is a serious command, so only I should be able to use it.",
]
DOC_NOTE = ("The user shared the text below. Base your answer on it and do "
            "not invent details that are not in it.")

ORB_HOUSING = "#07141c"
ORB_COLORS = {"idle": "#8b6fd0", "listening": "#c9bfe8", "thinking": "#8b8299",
              "speaking": "#b7a3dd", "muted": "#6b6b6b"}
ORB_STYLES = ("logo", "reactor", "hud", "pulse")

# shared state
tts = None
model = None
BEAM = 1
THRESHOLD = 0.03
FOLDERS, FILES, APPS = {}, {}, {}
state = {"muted": False, "ptt_only": False}
wake_model = None
speaker = {"extractor": None, "print": None}
orb_state = {"mode": "idle", "level": 0.0}
orb_cmds = queue.Queue()
wake_queue = queue.Queue()
typed_queue = queue.Queue()        # commands typed in the control panel
chat_history = collections.deque(maxlen=60)   # recent chat lines for the panel
chat_listeners = []                # open panels waiting for new chat lines
tray_ref = {}                      # the tray icon and its two pictures
ollama_lock = threading.Lock()
speak_gen = {"n": 0}
stop_epoch = {"n": 0}    # goes up every time the user cuts Optimus off
reply_epoch = {"n": 0}   # value of stop_epoch when the current command began
working = {"on": False}  # True from hearing a command until it is fully spoken
dictation = {"on": False}
quiz = {"topic": None}
pending_remote = {"until": 0}
subtitle_queue = queue.Queue()
speech_queue = queue.Queue()
audio_queue = queue.Queue(maxsize=3)
announce_queue = queue.Queue()
alarm_lock = threading.RLock()
alarms = []
shots = []
history = []
_loc_cache = {}
settings = {}
news_cache = {"titles": []}
online_state = {"fail_until": 0, "warned": False}
_lock_socket = None
_TIMEOUT = object()
_ocr = {"engine": None}


# ======================== small helpers ========================
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def clean(text):
    return re.sub(r"[*_#`]", "", text).strip()


SPOKEN_FIXES = [
    (r"https?://\S+", " "),
    (r"\be\.g\.", "for example"),
    (r"\bi\.e\.", "that is"),
    (r"\betc\.", "and so on"),
    (r"\bvs\b\.?", "versus"),
    (r"(\d)\s?°\s?C\b", r"\1 degrees Celsius"),
    (r"(\d)\s?°\s?F\b", r"\1 degrees Fahrenheit"),
    (r"°", " degrees"),
    (r"(\d)\s?%", r"\1 percent"),
    (r"₹\s?(\d+(?:,\d{2,3})*(?:\.\d+)?)", r"\1 rupees"),
    (r"\$\s?(\d+(?:,\d{2,3})*(?:\.\d+)?)", r"\1 dollars"),
    (r"\s*&\s*", " and "),
    (r"\band/or\b", "and or"),
    (r"(\w)/(\w)", r"\1 or \2"),
    (r"\s*[–—]+\s*", ", "),
    (r"\s-\s", ", "),
    (r"\.{2,}|…", ", "),
    (r"[()\[\]{}]", ", "),
]


def speakable(text):
    """Rewrite text the way a person would say it out loud."""
    for pattern, repl in SPOKEN_FIXES:
        text = re.sub(pattern, repl, text, flags=re.I)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",(\s*,)+", ",", text)
    text = re.sub(r",\s*([.!?])", r"\1", text)
    text = re.sub(r",\s*$", ".", text)       # a trailing pause ends the line
    text = re.sub(r"^[,\s]+", "", text)
    return " ".join(text.split())


def http_get(url, timeout=8):
    """Download a web page. Gives up cleanly, even if DNS hangs."""
    box = {}

    def work():
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT,
                              "Accept-Language": "en"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                box["data"] = response.read().decode("utf-8",
                                                     errors="replace")
        except Exception as error:
            box["error"] = error

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(timeout + 3)
    if "data" in box:
        return box["data"]
    raise box.get("error") or TimeoutError("timed out: " + url)


def run_with_timeout(fn, args, seconds):
    box = {}

    def work():
        try:
            box["value"] = fn(*args)
        except Exception as error:
            box["error"] = error

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        return _TIMEOUT
    if "error" in box:
        raise box["error"]
    return box.get("value")


def ack():
    return random.choice(ACKS).format(n=USER_NAME)


def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            settings.update(json.load(f))
    except Exception:
        pass


_settings_lock = threading.Lock()


def save_setting(key, value):
    with _settings_lock:
        settings[key] = value
        try:
            tmp = SETTINGS_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(settings, f)
            os.replace(tmp, SETTINGS_FILE)
        except Exception:
            pass


def my_city():
    return settings.get("city") or HOME_CITY


def normalize_text(t):
    t = t.replace("wi fi", "wifi").replace("blue tooth", "bluetooth")
    t = re.sub(r"\b(the|s|is|about|like) (?:whether|wether|weathers)\b",
               r"\1 weather", t)
    for old in ("screen shots", "screen shot", "screen grab",
                "screen capture"):
        t = t.replace(old, "screenshot" + ("s" if old.endswith("s") else ""))
    return t


def numberize(text):
    """Turn number words into digits: 'twenty five' -> '25'."""
    text = (text.replace("an hour and a half", "90 minutes")
            .replace("half an hour", "30 minutes")
            .replace("half hour", "30 minutes")
            .replace("a quarter of an hour", "15 minutes"))
    tokens = text.split()
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in NUM_WORDS:
            value = NUM_WORDS[t]
            if (value >= 20 and i + 1 < len(tokens)
                    and tokens[i + 1] in NUM_WORDS
                    and 1 <= NUM_WORDS[tokens[i + 1]] <= 9):
                value += NUM_WORDS[tokens[i + 1]]
                i += 1
            out.append(str(value))
        else:
            out.append(t)
        i += 1
    return " ".join(out)


def parse_duration(text):
    """'5 minutes' -> 300 seconds. Returns None if no duration found."""
    total = 0.0
    found = False
    for m in re.finditer(
            r"(\d+(?:\.\d+)?|an|a)\s*(seconds?|secs?|minutes?|mins?|"
            r"hours?|hrs?)\b", text):
        number = 1.0 if m.group(1) in ("a", "an") else float(m.group(1))
        unit = m.group(2).rstrip("s")
        total += number * UNIT_SECONDS[unit]
        found = True
    return int(total) if found else None


def parse_clock(text):
    """'at 6 30 pm' -> timestamp of the next 6:30 PM. None if not found."""
    m = re.search(CLOCK_RE, text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    meridiem = (m.group(3) or "").replace(" ", "")
    if hour > 23 or minute > 59:
        return None
    now = datetime.now()
    options = []
    if meridiem == "am":
        options = [hour % 12]
    elif meridiem == "pm":
        options = [hour % 12 + 12]
    elif hour > 12 or hour == 0:
        options = [hour]
    else:
        options = [hour % 12, hour % 12 + 12]
    for h in options:
        due = now.replace(hour=h, minute=minute, second=0, microsecond=0)
        if due > now:
            return due.timestamp()
    due = now.replace(hour=options[0], minute=minute, second=0,
                      microsecond=0) + timedelta(days=1)
    return due.timestamp()


def format_duration(seconds):
    seconds = max(0, int(round(seconds)))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    if hours:
        parts.append("%d hour%s" % (hours, "" if hours == 1 else "s"))
    if minutes:
        parts.append("%d minute%s" % (minutes, "" if minutes == 1 else "s"))
    if secs and not hours:
        parts.append("%d second%s" % (secs, "" if secs == 1 else "s"))
    return " ".join(parts) if parts else "0 seconds"


def format_clock(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%I:%M %p").lstrip("0")


def reminder_label(text):
    t = re.sub(r"\b(remind me|set a reminder|set reminder|reminders?|"
               r"please|set an alarm|set alarm|alarms?)\b", " ", text)
    t = re.sub(DURATION_RE, " ", t)
    t = re.sub(r"\b(?:at|by|for)\s+\d{1,2}(?: \d{2})?\s*(?:a m|p m|am|pm)?\b",
               " ", t)
    t = " ".join(t.split())
    t = re.sub(r"^(to|about|that)\s+", "", t)
    return t.strip()


def first_sentences(text, count=2, limit=380):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = " ".join(parts[:count])
    return out if len(out) <= limit else out[:limit].rsplit(" ", 1)[0] + "."


# ======================== subtitles on screen ========================
def show_subtitle(text, seconds=0):
    subtitle_queue.put(("show", text, seconds))


def hide_subtitle(delay_ms=1500):
    subtitle_queue.put(("hide", delay_ms, 0))


def set_orb(mode):
    orb_state["mode"] = mode


def mix_color(c1, c2, t):
    """Blend two '#rrggbb' colours. t=0 gives c1, t=1 gives c2."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[k] + (b[k] - a[k]) * t)
                                   for k in range(3))


def draw_reactor(c, size, color, hover, angle, pulse, look):
    cx = cy = size / 2.0
    big = size * 0.46
    c.create_oval(cx - big, cy - big, cx + big, cy + big, fill=ORB_HOUSING,
                  outline=mix_color(color, ORB_HOUSING, 0.4), width=2)
    w = max(3, int(size * 0.045))
    r1 = size * 0.38
    for i in range(3):
        c.create_arc(cx - r1, cy - r1, cx + r1, cy + r1,
                     start=angle + i * 120, extent=78, style="arc",
                     outline=color, width=w)
    r2 = size * 0.28
    for i in range(4):
        c.create_arc(cx - r2, cy - r2, cx + r2, cy + r2,
                     start=-angle * 1.6 + i * 90, extent=48, style="arc",
                     outline=mix_color(color, ORB_HOUSING, 0.35),
                     width=max(2, w - 1))
    for i in range(6):
        a = math.radians(angle * 0.5 + i * 60)
        c.create_line(cx + math.cos(a) * size * 0.14,
                      cy - math.sin(a) * size * 0.14,
                      cx + math.cos(a) * size * 0.22,
                      cy - math.sin(a) * size * 0.22,
                      fill=mix_color(color, ORB_HOUSING, 0.5), width=2)
    core = size * (0.095 + 0.03 * pulse + 0.03 * hover)
    ox, oy = look
    for k in (3, 2, 1):
        g = core + k * size * 0.022
        c.create_oval(cx + ox - g, cy + oy - g, cx + ox + g, cy + oy + g,
                      outline=mix_color(color, ORB_HOUSING, 0.35 + 0.2 * k),
                      width=2)
    c.create_oval(cx + ox - core, cy + oy - core, cx + ox + core,
                  cy + oy + core,
                  fill=mix_color(color, "#ffffff", 0.25 * hover), outline="")


def draw_hud(c, size, color, hover, angle, pulse, look):
    cx = cy = size / 2.0
    big = size * 0.46
    c.create_oval(cx - big, cy - big, cx + big, cy + big, fill=ORB_HOUSING,
                  outline=mix_color(color, ORB_HOUSING, 0.4), width=2)
    rt = size * 0.40
    for i in range(36):
        a = math.radians(angle * 0.4 + i * 10)
        long_tick = (i % 3 == 0)
        r_in = rt - (size * 0.05 if long_tick else size * 0.025)
        c.create_line(cx + math.cos(a) * rt, cy - math.sin(a) * rt,
                      cx + math.cos(a) * r_in, cy - math.sin(a) * r_in,
                      fill=color if long_tick
                      else mix_color(color, ORB_HOUSING, 0.5),
                      width=2 if long_tick else 1)
    r2 = size * 0.29
    for i in range(2):
        c.create_arc(cx - r2, cy - r2, cx + r2, cy + r2,
                     start=-angle * 1.3 + i * 180, extent=110, style="arc",
                     outline=color, width=3)
    r3 = size * 0.20
    soft = mix_color(color, ORB_HOUSING, 0.55)
    c.create_oval(cx - r3, cy - r3, cx + r3, cy + r3, outline=soft, width=1)
    c.create_line(cx - r3, cy, cx + r3, cy, fill=soft)
    c.create_line(cx, cy - r3, cx, cy + r3, fill=soft)
    core = size * (0.05 + 0.02 * pulse + 0.02 * hover)
    ox, oy = look
    c.create_oval(cx + ox - core, cy + oy - core, cx + ox + core,
                  cy + oy + core, fill=color, outline="")


def draw_pulse(c, size, color, hover, angle, pulse, look):
    cx = cy = size / 2.0
    big = size * 0.46
    c.create_oval(cx - big, cy - big, cx + big, cy + big, fill=ORB_HOUSING,
                  outline=mix_color(color, ORB_HOUSING, 0.4), width=2)
    ring = size * (0.30 + 0.08 * pulse + 0.04 * hover)
    c.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline=color,
                  width=3)
    inner = size * 0.20
    c.create_oval(cx - inner, cy - inner, cx + inner, cy + inner,
                  outline=mix_color(color, ORB_HOUSING, 0.5), width=1)
    core = size * (0.09 + 0.03 * pulse + 0.02 * hover)
    ox, oy = look
    c.create_oval(cx + ox - core, cy + oy - core, cx + ox + core,
                  cy + oy + core, fill=color, outline="")


def prepare_logo(path):
    """Load your logo and cut it into a clean circle."""
    from PIL import Image, ImageDraw
    img = Image.open(path).convert("RGBA")
    alpha = np.asarray(img.getchannel("A"))
    if alpha.min() < 250:
        # already cut out (has transparent corners): just make it square
        side = max(img.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        return square
    arr = np.asarray(img.convert("RGB"))
    dark = (arr[:, :, 0] < 70) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
    ys, xs = np.where(dark)
    side = min(img.size)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    if len(xs) > 0.15 * img.width * img.height:
        # a dark round badge: crop tightly around it
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        side = int(max(x1 - x0, y1 - y0)) + 1
        left = int((x0 + x1) / 2 - side / 2)
        top = int((y0 + y1) / 2 - side / 2)
    crop = img.crop((left, top, left + side, top + side))
    big = 4
    mask = Image.new("L", (side * big, side * big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, side * big - 1, side * big - 1),
                                 fill=255)
    crop.putalpha(mask.resize((side, side), Image.LANCZOS))
    return crop


def work_area():
    """The part of the screen not covered by the taskbar."""
    try:
        import ctypes.wintypes as wt
        rect = wt.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        if rect.right > rect.left and rect.bottom > rect.top:
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None


def snap_target(x, y, size, area, margin=8, reach=90):
    """Where the orb should settle so it sits neatly against an edge."""
    left, top, right, bottom = area
    if abs(x - (left + margin)) < reach:
        x = left + margin
    elif abs((x + size) - (right - margin)) < reach:
        x = right - margin - size
    if abs(y - (top + margin)) < reach:
        y = top + margin
    elif abs((y + size) - (bottom - margin)) < reach:
        y = bottom - margin - size
    return int(x), int(y)


def logo_photo(fx, side, angle, muted):
    from PIL import Image, ImageEnhance, ImageTk
    q = int(round(angle / 3.0))
    cache_key = (side, q, muted)
    photo = fx.cache.get(cache_key)
    if photo is None:
        if len(fx.cache) > 220:
            fx.cache.clear()
        img = fx.base.resize((side, side), Image.LANCZOS)
        if q:
            img = img.rotate(q * 3, resample=Image.BICUBIC)
        if muted:
            rgb = ImageEnhance.Brightness(img.convert("RGB")).enhance(0.45)
            rgb.putalpha(img.getchannel("A"))
            img = rgb
        background = Image.new("RGB", (side, side), (1, 2, 3))
        background.paste(img, (0, 0), img)
        photo = ImageTk.PhotoImage(background)
        fx.cache[cache_key] = photo
    return photo


def fx_spawn(fx, mode, size, level):
    cx = cy = size / 2.0
    big = size * 0.30
    kind = "flake" if random.random() < 0.35 else "dust"
    a = random.uniform(0, 2 * math.pi)
    p = {"kind": kind, "age": 0.0, "spin": random.uniform(-3, 3),
         "rot": random.uniform(0, 6.28),
         "r": (random.uniform(1.5, 3.2) if kind == "dust"
               else random.uniform(3.0, 5.0))}
    ca, sa = math.cos(a), math.sin(a)
    if mode == "listening":
        rad = size * 0.49
        p.update(x=cx + ca * rad, y=cy - sa * rad, vx=-ca * 45, vy=sa * 45,
                 life=1.4)
    elif mode == "speaking":
        rad = big * 1.15
        sp = 35 + 90 * level * random.random()
        p.update(x=cx + ca * rad, y=cy - sa * rad, vx=ca * sp, vy=-sa * sp,
                 life=random.uniform(0.7, 1.3))
    elif mode == "thinking":
        rad = random.uniform(big * 1.25, big * 1.55)
        p.update(x=cx + ca * rad, y=cy - sa * rad, vx=-sa * 70, vy=-ca * 70,
                 life=random.uniform(1.5, 2.5))
    else:
        rad = random.uniform(big * 1.3, big * 1.6)
        sp = random.uniform(6, 14) * random.choice((-1, 1))
        p.update(x=cx + ca * rad, y=cy - sa * rad, vx=-sa * sp, vy=-ca * sp,
                 life=random.uniform(3.0, 6.0))
    fx.particles.append(p)


def fx_burst(fx, size, now, count=28):
    cx = cy = size / 2.0
    big = size * 0.30
    for _ in range(count):
        a = random.uniform(0, 2 * math.pi)
        sp = random.uniform(60, 170)
        kind = "flake" if random.random() < 0.5 else "dust"
        fx.particles.append({
            "kind": kind, "age": 0.0, "life": random.uniform(0.6, 1.2),
            "x": cx + math.cos(a) * big, "y": cy - math.sin(a) * big,
            "vx": math.cos(a) * sp, "vy": -math.sin(a) * sp,
            "spin": random.uniform(-6, 6), "rot": random.uniform(0, 6.28),
            "r": (random.uniform(1.5, 3.2) if kind == "dust"
                  else random.uniform(3.0, 5.5))})
    fx.rings.append((now, 0.9))
    fx.scale_v += 3.0
    fx.wobble_v += random.choice((-1, 1)) * 60


def fx_update(fx, dt, size, mode, curx, cury, hover):
    cx = cy = size / 2.0
    alive = []
    for p in fx.particles:
        p["age"] += dt
        if p["age"] >= p["life"]:
            continue
        ddx, ddy = p["x"] - curx, p["y"] - cury
        d = math.hypot(ddx, ddy)
        if hover > 0.05 and d > 0.5:
            if d < size * 0.22:  # scatter away from the cursor
                push = (1 - d / (size * 0.22)) * 260 * dt
                p["vx"] += ddx / d * push
                p["vy"] += ddy / d * push
            else:  # drift gently towards it
                p["vx"] -= ddx / d * 40 * hover * dt
                p["vy"] -= ddy / d * 40 * hover * dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        if mode != "listening":
            p["vx"] *= (1 - 0.5 * dt)
            p["vy"] *= (1 - 0.5 * dt)
        p["rot"] += p["spin"] * dt
        dist = math.hypot(p["x"] - cx, p["y"] - cy)
        if dist > size * 0.5 or (mode == "listening"
                                 and dist < size * 0.34):
            continue
        alive.append(p)
    fx.particles = alive


# ---- colour themes: Infinity Stones, hero palettes, or your own ----
STONES = [("Power", "#a855f7"), ("Space", "#3b82f6"), ("Reality", "#ef4444"),
          ("Soul", "#f59e0b"), ("Mind", "#facc15"), ("Time", "#22c55e")]
DEFAULT_THEME = "Vibranium"
THEMES = {
    "Vibranium": ("#8b6fd0", "#c9bfe8"),
    "Midnight Silver": ("#c8ccd6", "#6f7b92"),
    "Royal Violet": ("#7c4dff", "#b9a2ff"),
    "Arctic": ("#7dd3fc", "#e0f2fe"),
    "Graphite": ("#e5e7eb", "#6b7280"),
    "Platinum Gold": ("#d9b45a", "#f3e6bf"),
    "Rose Gold": ("#e0a899", "#f6dcd3"),
    "Emerald": ("#34d399", "#a7f3d0"),
    "Cobalt": ("#4f7cff", "#a5b8ff"),
    "Crimson": ("#e5484d", "#f5a3a6"),
    "Ember": ("#f59e0b", "#fcd34d"),
    "Ocean": ("#14b8a6", "#99f6e4"),
    "Orchid": ("#c084fc", "#f0abfc"),
    "Spectrum": None,                       # slowly drifts through colours
    "Custom": None,                         # the two colours you pick
}
SPECTRUM = ["#8b6fd0", "#4f7cff", "#14b8a6", "#34d399", "#d9b45a", "#e5484d"]


def _hex_mix(a, b, t):
    return mix_color(a, b, max(0.0, min(1.0, t)))


def theme_colors():
    """(first colour, second colour) of the theme you picked."""
    name = settings.get("theme", DEFAULT_THEME)
    if name == "Custom":
        return (settings.get("custom_a", "#8b6fd0"),
                settings.get("custom_b", "#c9bfe8"))
    if name == "Spectrum":
        pos = (time.time() * 0.12) % len(SPECTRUM)
        i, frac = int(pos), pos - int(pos)
        n = len(SPECTRUM)
        a = _hex_mix(SPECTRUM[i], SPECTRUM[(i + 1) % n], frac)
        b = _hex_mix(SPECTRUM[(i + 3) % n], SPECTRUM[(i + 4) % n], frac)
        return a, b
    return THEMES.get(name) or THEMES[DEFAULT_THEME]


class OrbFX:
    """Springs, particles, orbits and ripples for the logo orb."""

    def __init__(self):
        self.particles = []
        self.rings = []
        self.scale = 1.0
        self.scale_v = 0.0
        self.wobble = 0.0
        self.wobble_v = 0.0
        self.last_ring = 0.0
        self.cache = {}
        self.base = None
        self.base_failed = False
        self.photo = None
        self.orbit_t = 0.0      # how far the orbiting sparks have travelled
        self.wave_t = 0.0       # clock for the voice waves
        self.speed = 0.6        # smoothed orbit speed
        self.flare = 0.0        # sparks swell while the voice is loud


def _tilted(cx, cy, a, b, tilt, theta):
    x, y = a * math.cos(theta), b * math.sin(theta)
    ct, st = math.cos(tilt), math.sin(tilt)
    return cx + x * ct - y * st, cy + x * st + y * ct


def _spark(c, x, y, r, fill, shape):
    if shape == "diamond":
        c.create_polygon(x, y - r * 1.3, x + r, y, x, y + r * 1.3, x - r, y,
                         fill=fill, outline="")
    elif shape == "star":
        pts = []
        for k in range(8):
            ang = k * math.pi / 4
            rr = r * 1.7 if k % 2 == 0 else r * 0.55
            pts.extend((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
        c.create_polygon(pts, fill=fill, outline="")
    else:
        c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="")


def draw_orbits(c, fx, size, dt, mode, level, colors, key, front):
    """Sparks that orbit the logo on tilted rings. front=False draws the half
    behind the logo, front=True the half in front of it."""
    count = max(0, min(8, int(settings.get("orbit_count", 3))))
    if count == 0:
        return
    cx = cy = size / 2.0
    pa, pb = colors
    if not front:
        base = {"idle": 0.55, "listening": 1.0, "thinking": 2.6,
                "speaking": 1.3}.get(mode, 0.5)
        want = base * float(settings.get("orbit_speed", 1.0))
        if mode in ("speaking", "listening"):
            want *= 1.0 + 1.2 * level
        fx.speed += (want - fx.speed) * min(1.0, 4 * dt)
        fx.orbit_t += fx.speed * dt
        fx.flare += (level - fx.flare) * min(1.0, 10 * dt)
    show_paths = bool(settings.get("orbit_paths", True))
    for i in range(count):
        tilt = math.radians(-35 + i * (180.0 / count) + 12 * (i % 2))
        a = size * (0.455 if i % 2 == 0 else 0.42)
        b = a * (0.30 + 0.07 * (i % 3))
        direction = 1 if i % 2 == 0 else -1
        col = pa if i % 2 == 0 else pb
        if not front and show_paths:
            pts = []
            for k in range(49):
                px, py = _tilted(cx, cy, a, b, tilt, k * math.pi / 24.0)
                pts.extend((px, py))
            c.create_line(pts, fill=mix_color(col, key, 0.86), width=1,
                          smooth=True)
        theta = direction * fx.orbit_t * 1.6 + i * 2.1
        tail = max(0, min(14, int(settings.get("orbit_trail", 8))))
        shape = settings.get("spark_shape", "dot")
        grow = float(settings.get("spark_size", 1.0))
        for trail in range(tail, -1, -1):
            th = theta - direction * trail * 0.10
            depth = math.sin(th)
            if (depth >= 0) != front:
                continue
            px, py = _tilted(cx, cy, a, b, tilt, th)
            fade = 1.0 - trail / float(tail + 1)
            r = (size * 0.016 * (1 + 0.5 * depth) + 1.5) * grow
            r *= (0.35 + 0.65 * fade) * (1 + 0.7 * fx.flare)
            r = min(r, size * 0.06)
            tone = mix_color(col, "#ffffff", 0.55 if trail == 0 else 0.0)
            _spark(c, px, py, r, mix_color(tone, key, 1 - fade * 0.95),
                   shape)
            if trail == 0 and fx.flare > 0.15:
                g = r * (1.8 + fx.flare)
                c.create_oval(px - g, py - g, px + g, py + g,
                              outline=mix_color(col, key, 0.45), width=1)


def draw_voice_waves(c, fx, size, now, mode, level, colors, key, big):
    """Living rings and bars that follow how loud the voice is."""
    style = settings.get("wave_style", "both")
    if style == "off":
        return
    cx = cy = size / 2.0
    pa, pb = colors
    gain = float(settings.get("wave_gain", 1.0))
    level = min(1.0, level * gain)
    if mode == "speaking":
        amp = level
    elif mode == "listening":
        amp = 0.8 * level
    else:
        amp = 0.04
    if style in ("ring", "both"):
        t = now * (3.0 + 6.0 * amp)
        for k, (col, width) in enumerate(((pa, 3), (pb, 2), ("#ffffff", 1))):
            r0 = big * 1.15 + k * size * 0.018
            swing = size * (0.006 + 0.07 * amp) * (1.0 - 0.18 * k)
            pts = []
            for n in range(73):
                ang = n * 2 * math.pi / 72.0
                wob = (math.sin(3 * ang + t + k) * 0.5
                       + math.sin(5 * ang - t * 1.3 + k * 2) * 0.3
                       + math.sin(9 * ang + t * 1.9) * 0.2)
                r = r0 + swing * wob
                pts.extend((cx + math.cos(ang) * r, cy - math.sin(ang) * r))
            tone = col if k < 2 else mix_color("#ffffff", key, 0.4)
            c.create_line(pts, fill=mix_color(tone, key, 0.25 if amp < 0.1
                                              else 0.0),
                          width=width, smooth=True)
    if style in ("bars", "both") and mode in ("speaking", "listening"):
        r_in = big * 1.14 + (size * 0.04 if style == "both" else 0)
        for i in range(48):
            a = math.radians(i * 360.0 / 48 + now * 25)
            wave = 0.5 + 0.5 * (math.sin(now * 9 + i * 0.9)
                                * math.sin(now * 3.1 + i * 0.37))
            length = size * (0.012 + 0.07 * level * (0.35 + wave))
            ca, sa = math.cos(a), math.sin(a)
            c.create_line(cx + ca * r_in, cy - sa * r_in,
                          cx + ca * (r_in + length),
                          cy - sa * (r_in + length),
                          fill=pa if i % 2 == 0 else pb, width=2)


def draw_logo_orb(c, fx, size, now, dt, mode, hover, level, dx, dy, dist,
                  curx, cury, key):
    cx = cy = size / 2.0
    scale_logo = max(0.5, min(1.3, float(settings.get("logo_scale", 1.0))))
    big = size * 0.30 * scale_logo  # radius of the logo
    muted = mode == "muted"
    pa, pb = theme_colors()
    if muted:
        color, other = "#6b6b6b", "#4a4a4a"
    else:
        color = {"idle": pb, "listening": mix_color(pb, "#ffffff", 0.35),
                 "thinking": pa, "speaking": pa}.get(mode, pb)
        custom = (settings.get("mode_colors") or {}).get(mode)
        if custom:
            color = custom
        other = pb if color == pa else pa
    color = mix_color(color, "#ffffff", hover * 0.25)
    dim = mix_color(color, key, 0.55)
    faint = mix_color(color, key, 0.78)
    colors = (pa, pb) if not muted else (color, other)

    # springs: the logo bounces, swings and breathes
    target = 1.0
    if not muted:
        target += 0.10 * hover
        if mode in ("speaking", "listening"):
            target += 0.07 * level
    fx.scale_v += (target - fx.scale) * 90 * dt
    fx.scale_v *= max(0.0, 1.0 - 9 * dt)
    fx.scale = max(0.85, min(1.35, fx.scale + fx.scale_v * dt))
    fx.wobble_v += -fx.wobble * 60 * dt
    fx.wobble_v *= max(0.0, 1.0 - 6 * dt)
    fx.wobble = max(-25.0, min(25.0, fx.wobble + fx.wobble_v * dt))

    # ripples (hover, click, listening)
    fx.rings = [(t0, s) for (t0, s) in fx.rings if now - t0 < 0.9]
    if mode == "listening" and now - fx.last_ring > 0.38:
        fx.last_ring = now
        fx.rings.append((now, 0.4 + level))
    for t0, strength in fx.rings:
        age = now - t0
        r = big * 1.10 + age * size * 0.20
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      outline=mix_color(color, key, age / 0.9),
                      width=2 if strength < 0.8 else 3)

    # orbiting sparks (the half behind the logo)
    if not muted:
        draw_orbits(c, fx, size, dt, mode, level, colors, key, False)

    # mode rings
    ring_style = settings.get("ring_style", "rings")
    if (mode == "idle" or muted) and ring_style != "none":
        breathe = 0.0 if muted else math.sin(now * 1.4) * size * 0.012
        for i, r in enumerate((big * 1.20, big * 1.38)):
            rr = r + breathe * (1 + i)
            if ring_style == "segments":
                for seg in range(24):
                    c.create_arc(cx - rr, cy - rr, cx + rr, cy + rr,
                                 start=seg * 15 + now * (20 if i else -20),
                                 extent=9, style="arc",
                                 outline=dim if i == 0 else faint,
                                 width=3 if i == 0 else 2)
            else:
                c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr,
                              outline=dim if i == 0 else faint,
                              width=2 if i == 0 else 1)
        if not muted:
            r = big * 1.30
            for k, extent in ((0, 70), (180, 40)):
                c.create_arc(cx - r, cy - r, cx + r, cy + r,
                             start=(now * 40 + k) % 360, extent=extent,
                             style="arc", outline=color, width=2)
    elif mode == "thinking":
        r = big * 1.28
        for k, extent in ((0, 120), (180, 60)):
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=(-now * 220 + k) % 360, extent=extent,
                         style="arc", outline=color, width=3)
        for k in range(3):
            for trail in range(4):
                a = math.radians(now * 260 - k * 120 - trail * 9)
                px, py = cx + math.cos(a) * r, cy - math.sin(a) * r
                s = 4 - trail
                c.create_oval(px - s, py - s, px + s, py + s,
                              fill=mix_color(color, key, trail * 0.22),
                              outline="")
    if not muted and mode in ("speaking", "listening"):
        draw_voice_waves(c, fx, size, now, mode, level, colors, key, big)

    # dust and flakes
    pstyle = settings.get("particle_style", "dust")
    if (muted or not settings.get("particles", True) or pstyle == "none"):
        fx.particles = []
    else:
        want = {"idle": 10, "listening": 22, "thinking": 16,
                "speaking": 20}.get(mode, 10)
        want = int(want * float(settings.get("particle_density", 1.0)))
        if len(fx.particles) < want and random.random() < 0.5:
            fx_spawn(fx, mode, size, level)
            fresh = fx.particles[-1]
            if pstyle == "stars":
                fresh["kind"] = "flake"
                fresh["r"] = max(fresh["r"], 3.5)
            elif pstyle == "embers":
                fresh["kind"] = "dust"
                fresh["vy"] = fresh.get("vy", 0) - 38
        fx_update(fx, dt, size, mode, curx, cury, hover)
        for p in fx.particles:
            fade = math.sin(math.pi * p["age"] / p["life"])
            col = mix_color(color, key, 1 - fade * 0.9)
            x, y, r = p["x"], p["y"], p["r"]
            if p["kind"] == "dust":
                c.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="")
            else:
                pts = []
                for k in range(8):
                    a = p["rot"] + k * math.pi / 4
                    rr = r if k % 2 == 0 else r * 0.35
                    pts.extend((x + math.cos(a) * rr, y - math.sin(a) * rr))
                c.create_polygon(pts, fill=col, outline="")

    # the logo itself: upright, bouncing, leaning towards your cursor
    bob = 0.0 if muted else (math.sin(now * 1.6) * size * 0.008
                             * float(settings.get("orb_bob", 1.0)))
    fx.spin_angle = (getattr(fx, "spin_angle", 0.0)
                     + float(settings.get("logo_spin", 0.0)) * dt) % 360.0
    offx = offy = 0.0
    if dist > 1 and hover > 0.02:
        k = min(size * 0.035, dist / 30.0) * hover
        offx, offy = dx / dist * k, dy / dist * k
    lx, ly = cx + offx, cy + offy + bob
    side = max(8, int(2 * big * fx.scale) // 2 * 2)
    photo = logo_photo(fx, side, fx.wobble + fx.spin_angle, muted)
    fx.photo = photo
    c.create_image(lx, ly, image=photo)
    if not muted:
        glint = (now * (90 if hover > 0.1 else 35)) % 360
        r = side / 2.0 - 1
        c.create_arc(lx - r, ly - r, lx + r, ly + r, start=glint, extent=26,
                     style="arc", outline="#d8f6ff", width=2)
        # orbiting sparks (the half in front of the logo)
        draw_orbits(c, fx, size, dt, mode, level, colors, key, True)


def toggle_mute_state():
    state["muted"] = not state["muted"]


def toggle_lock_state():
    save_setting("voice_lock", not lock_enabled())


def orb_command(t, words):
    if (("customize" in words or "customise" in words
         or "personalize" in words or "personalise" in words)
            and len(words) <= 4) or any(
                p in t for p in ("your panel", "your control panel",
                                 "your settings", "your window")):
        orb_cmds.put(("panel",))
        return "Opening my control panel."
    if "orb" not in words:
        return None
    aliases = {"image": "logo", "picture": "logo"}
    for name in list(ORB_STYLES) + list(aliases):
        if name in words:
            target = aliases.get(name, name)
            if target == "logo" and not os.path.exists(current_logo_path()):
                return ("Put a picture called %s in my folder first, or pick "
                        "a logo in my control panel." % ORB_IMAGE)
            orb_cmds.put(("style", target))
            return "Orb style changed to %s." % target
    if any(w in words for w in ("bigger", "larger", "increase")):
        orb_cmds.put(("size", 20))
        return "Bigger it is."
    if any(w in words for w in ("smaller", "decrease")):
        orb_cmds.put(("size", -20))
        return "Smaller it is."
    if "reset" in words or "corner" in words:
        orb_cmds.put(("reset",))
        return "Orb back in its corner."
    if "hide" in words:
        orb_cmds.put(("visible", False))
        return "Orb hidden. Say show orb to bring it back."
    if "show" in words:
        orb_cmds.put(("visible", True))
        return "Here it is."
    return None


# ======================== logo pack ========================
# Thirteen original red-and-blue emblems, drawn by the code the first time and
# saved in the "logos" folder. Drop your own PNGs there (or use the panel) to
# add more of your own.
LOGO_DIR = os.path.join(BASE_DIR, "logos")
LOGO_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
_logo_lock = threading.Lock()
HERO_RED = "#ff3347"
HERO_BLUE = "#2f8cff"
# the old built-in logos from earlier versions get removed from your folder
OLD_LOGO_NAMES = ("neon_core", "hexa", "guardian", "volt", "watcher",
                  "pulse_wave", "orbit", "prism", "crescent", "circuit",
                  "gem", "galaxy")


def _outline(d, points, c, width):
    d.line(list(points) + [points[0]], fill=c, width=width, joint="curve")


def _polar(r, deg, cx=512, cy=512):
    return (cx + r * math.cos(math.radians(deg)),
            cy + r * math.sin(math.radians(deg)))


def _mirror(points):
    return [(1024 - x, y) for x, y in points]


def glyph_vanguard(d, layer, a, b):
    for y0, col in ((250, a), (385, b), (520, a)):
        d.polygon([(512, y0), (712, y0 + 155), (712, y0 + 245),
                   (512, y0 + 90), (312, y0 + 245), (312, y0 + 155)],
                  fill=col)


def glyph_nova(d, layer, a, b):
    pts = []
    for i in range(16):
        r = (330, 80, 235, 80)[i % 4]
        pts.append(_polar(r, -90 + i * 22.5))
    d.polygon(pts, fill=a)
    small = [_polar((150, 50, 110, 50)[i % 4], -90 + i * 22.5)
             for i in range(16)]
    d.polygon(small, fill=b)
    d.ellipse((472, 472, 552, 552), fill="#ffffff")


def glyph_thunder(d, layer, a, b):
    bolt = [(590, 180), (290, 580), (468, 580), (418, 850), (734, 420),
            (546, 420), (640, 180)]
    d.polygon(bolt, fill=a)
    d.line(bolt + [bolt[0]], fill=b, width=18, joint="curve")


def glyph_phoenix(d, layer, a, b):
    for tip, base in (((800, 285), 430), ((830, 385), 470),
                      ((810, 490), 510), ((755, 590), 550)):
        wing = [(548, base), (548, base + 64), tip]
        d.polygon(wing, fill=a)
        d.polygon(_mirror(wing), fill=a)
    d.polygon([(512, 300), (566, 450), (544, 640), (512, 730), (480, 640),
               (458, 450)], fill=b)
    d.ellipse((482, 240, 542, 300), fill=b)
    for tip in ((512, 840), (450, 790), (574, 790)):
        d.polygon([(512, 690), (tip[0] - 26, tip[1] - 90), tip,
                   (tip[0] + 26, tip[1] - 90)], fill=a)


def glyph_sentinel(d, layer, a, b):
    _outline(d, [(512, 200), (822, 512), (512, 824), (202, 512)], a, 24)
    top = [(300 + 424 * i / 30.0, 512 - 125 * math.sin(math.pi * i / 30.0))
           for i in range(31)]
    bottom = [(300 + 424 * i / 30.0, 512 + 125 * math.sin(math.pi * i / 30.0))
              for i in range(30, -1, -1)]
    d.polygon(top + bottom, fill=b)
    d.ellipse((447, 447, 577, 577), fill=a)
    d.ellipse((487, 487, 527, 527), fill="#ffffff")


def glyph_aegis(d, layer, a, b):
    outer = [(512, 205), (745, 290), (745, 525), (512, 835), (279, 525),
             (279, 290)]
    d.polygon(outer, fill=a)
    d.polygon([(512, 205), (279, 290), (279, 525), (512, 835)], fill=b)
    _outline(d, outer, "#ffffff", 14)
    d.line([(390, 450), (512, 575), (634, 450)], fill="#ffffff", width=28,
           joint="curve")


def glyph_comet(d, layer, a, b):
    d.polygon([(560, 395), (655, 470), (215, 815)], fill=b)
    d.polygon([(520, 330), (600, 405), (280, 700), (330, 560)], fill=a)
    d.ellipse((520, 280, 740, 500), fill="#ffffff")
    d.ellipse((545, 305, 715, 475), fill=a)
    for x, y, r in ((730, 640, 18), (610, 700, 12), (780, 300, 14)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=b)


def glyph_atom(d, layer, a, b):
    from PIL import Image, ImageDraw
    for i, deg in enumerate((0, 60, 120)):
        ring = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((196, 392, 828, 632),
                                     outline=a if i != 1 else b, width=18)
        layer.alpha_composite(ring.rotate(deg, resample=Image.BICUBIC,
                                          center=(512, 512)))
    d.ellipse((452, 452, 572, 572), fill="#ffffff")
    d.ellipse((472, 472, 552, 552), fill=a)


def glyph_crown(d, layer, a, b):
    d.polygon([(250, 640), (270, 380), (400, 510), (512, 320), (624, 510),
               (754, 380), (774, 640)], fill=a)
    d.rounded_rectangle((250, 665, 774, 735), radius=22, fill=b)
    for x, y in ((270, 380), (512, 320), (754, 380)):
        d.ellipse((x - 30, y - 30, x + 30, y + 30), fill="#ffffff")
    d.ellipse((482, 560, 542, 620), fill=b)


def glyph_target(d, layer, a, b):
    d.ellipse((252, 252, 772, 772), outline=a, width=22)
    d.ellipse((372, 372, 652, 652), outline=b, width=20)
    d.ellipse((472, 472, 552, 552), fill="#ffffff")
    for x0, y0, x1, y1 in ((512, 190, 512, 330), (512, 694, 512, 834),
                           (190, 512, 330, 512), (694, 512, 834, 512)):
        d.line((x0, y0, x1, y1), fill=a, width=24)


def glyph_flame(d, layer, a, b):
    d.polygon([(512, 190), (610, 330), (712, 450), (728, 585), (665, 715),
               (512, 815), (359, 715), (296, 585), (312, 450), (414, 330)],
              fill=a)
    d.polygon([(512, 350), (590, 470), (640, 590), (590, 710), (512, 770),
               (434, 710), (384, 590), (434, 470)], fill=b)
    d.polygon([(512, 520), (556, 610), (512, 700), (468, 610)],
              fill="#ffffff")


def glyph_jet(d, layer, a, b):
    d.polygon([(512, 185), (562, 390), (770, 575), (770, 655), (566, 600),
               (546, 745), (610, 800), (610, 845), (512, 815), (414, 845),
               (414, 800), (478, 745), (458, 600), (254, 655), (254, 575),
               (462, 390)], fill=a)
    d.polygon([(512, 285), (540, 400), (512, 470), (484, 400)], fill=b)
    for pts in ([(560, 500), (700, 600), (700, 626), (556, 570)],):
        d.polygon(pts, fill=b)
        d.polygon(_mirror(pts), fill=b)


def glyph_hexcore(d, layer, a, b):
    _outline(d, [_polar(310, 60 * i + 30) for i in range(6)], a, 26)
    d.polygon([_polar(190, 60 * i) for i in range(6)], fill=b)
    d.polygon([_polar(105, 60 * i + 30) for i in range(6)], fill=a)
    d.ellipse((472, 472, 552, 552), fill="#ffffff")


LOGO_PACK = [   # (file name, label, main colour, second colour, drawing)
    ("vanguard", "Vanguard", HERO_RED, HERO_BLUE, glyph_vanguard),
    ("nova", "Nova", HERO_BLUE, HERO_RED, glyph_nova),
    ("thunder", "Thunder", HERO_RED, HERO_BLUE, glyph_thunder),
    ("phoenix", "Phoenix", HERO_RED, HERO_BLUE, glyph_phoenix),
    ("sentinel", "Sentinel", HERO_BLUE, HERO_RED, glyph_sentinel),
    ("aegis", "Aegis", HERO_RED, HERO_BLUE, glyph_aegis),
    ("comet", "Comet", HERO_RED, HERO_BLUE, glyph_comet),
    ("atom", "Atom", HERO_BLUE, HERO_RED, glyph_atom),
    ("crown", "Crown", HERO_RED, HERO_BLUE, glyph_crown),
    ("target", "Target", HERO_RED, HERO_BLUE, glyph_target),
    ("flame", "Flame", HERO_RED, HERO_BLUE, glyph_flame),
    ("jet", "Jet", HERO_BLUE, HERO_RED, glyph_jet),
    ("hexcore", "Hexcore", HERO_BLUE, HERO_RED, glyph_hexcore),
]


def render_logo(a, b, glyph):
    """A dark round badge with a two-tone ring and glowing symbol (512 px)."""
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    s = 1024
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    dist = np.clip(np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / (s / 2),
                   0, 1)[..., None]
    u = ((xx + yy) / (2.0 * s))[..., None]          # 0 top-left, 1 bottom-right
    ca = np.array([int(a[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    cb = np.array([int(b[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    tint = cb * (1 - u) + ca * u
    rgb = (np.array([14, 20, 44], np.float32) * (1 - dist)
           + np.array([4, 6, 16], np.float32) * dist
           + tint * 0.20 * (1 - dist) ** 1.3)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8),
                          "RGB").convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse((20, 20, s - 21, s - 21), fill=255)
    d = ImageDraw.Draw(img)
    box = (22, 22, s - 23, s - 23)
    d.arc(box, start=135, end=315, fill=HERO_BLUE, width=22)
    d.arc(box, start=315, end=135, fill=HERO_RED, width=22)
    d.ellipse((64, 64, s - 65, s - 65), outline=(255, 255, 255, 40), width=3)
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    glyph(ImageDraw.Draw(layer), layer, a, b)
    glow = layer.filter(ImageFilter.GaussianBlur(24))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, layer)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return img.resize((512, 512), Image.LANCZOS)


def ensure_logo_pack():
    """Draw any built-in logo that is missing, and remove the old ones."""
    with _logo_lock:
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            for old in OLD_LOGO_NAMES:
                old_path = os.path.join(LOGO_DIR, old + ".png")
                if os.path.exists(old_path):
                    try:
                        keep = os.path.join(LOGO_DIR, "_old")
                        os.makedirs(keep, exist_ok=True)
                        os.replace(old_path, os.path.join(keep, old + ".png"))
                    except OSError:
                        pass
            for name, label, a, b, glyph in LOGO_PACK:
                path = os.path.join(LOGO_DIR, name + ".png")
                if not os.path.exists(path):
                    render_logo(a, b, glyph).save(path)
        except Exception as error:
            print("Couldn't draw the logo pack:", error)
    install_hero_logos()


def logo_label(fname):
    stem = os.path.splitext(fname)[0]
    match = re.match(r"hero_\d+_(.+)", stem)
    if match:
        stem = match.group(1)
    return stem.replace("_", " ").strip().title()


def list_logos():
    """[(label, path inside the folder)]: yours, your heroes, the built-in
    pack, then anything else in the folder."""
    items, seen = [], set()
    if os.path.exists(os.path.join(BASE_DIR, ORB_IMAGE)):
        items.append(("My Logo", ORB_IMAGE))
        seen.add(ORB_IMAGE)
    files = sorted(os.listdir(LOGO_DIR)) if os.path.isdir(LOGO_DIR) else []
    for fname in files:
        if (fname.startswith("hero_") and os.path.splitext(fname)[1].lower()
                in LOGO_EXTS):
            rel = "logos/" + fname
            items.append((logo_label(fname), rel))
            seen.add(rel)
    for name, label, a, b, glyph in LOGO_PACK:
        rel = "logos/%s.png" % name
        if os.path.exists(os.path.join(BASE_DIR, rel)):
            items.append((label, rel))
            seen.add(rel)
    for fname in files:
        rel = "logos/" + fname
        if (rel in seen
                or os.path.splitext(fname)[1].lower() not in LOGO_EXTS
                or os.path.splitext(fname)[0] in OLD_LOGO_NAMES):
            continue
        items.append((logo_label(fname), rel))
    return items


def find_logo(word):
    """The logo whose name contains this word, e.g. 'iron' -> Iron Man."""
    for label, rel in list_logos():
        if word.lower() in label.lower():
            return rel
    return None


def current_logo_path():
    """The logo file the orb and tray icon should use right now."""
    rel = settings.get("logo_file") or ORB_IMAGE
    path = os.path.join(BASE_DIR, rel)
    if os.path.exists(path):
        return path
    for label, rel in list_logos():
        return os.path.join(BASE_DIR, rel)
    return os.path.join(BASE_DIR, ORB_IMAGE)


# ======================== control panel ========================
PANEL_BG = "#000000"
PANEL_SIDE = "#050408"
PANEL_CARD = "#0b090f"
PANEL_CARD2 = "#16121e"
PANEL_EDGE = "#2b2238"
PANEL_TEXT = "#ece8f3"
PANEL_DIM = "#8b8299"
PANEL_ACCENTS = {"Matte Purple": "#7b5ea7", "Vibranium Silver": "#8f93a3",
                 "Royal Blue": "#4a6fa5", "Emerald": "#3f8f6b",
                 "Crimson": "#a8404a", "Antique Gold": "#a8863a",
                 "Rose": "#a8607f"}
PANEL_GOLD = "#7b5ea7"
PANEL_VIOLET = "#b7a3dd"
PANEL_RED = PANEL_GOLD
PANEL_BLUE = PANEL_VIOLET
PANEL_ACCENT = PANEL_GOLD
PANEL_INK = "#ffffff"


def apply_panel_theme():
    """Panel accent colour (Settings > Appearance)."""
    global PANEL_GOLD, PANEL_VIOLET, PANEL_RED, PANEL_BLUE, PANEL_ACCENT
    name = settings.get("panel_accent", "Matte Purple")
    base = (settings.get("panel_custom") if name == "Custom" else
            PANEL_ACCENTS.get(name)) or PANEL_ACCENTS["Matte Purple"]
    PANEL_GOLD = PANEL_RED = PANEL_ACCENT = base
    PANEL_VIOLET = PANEL_BLUE = mix_color(base, "#ffffff", 0.45)


PANEL_FONT = "Segoe UI"
QUICK_COMMANDS = ["What's the weather?", "What time is it?",
                  "Take a screenshot", "What's on my screen?",
                  "Minimize this window", "Set a timer for 5 minutes",
                  "Tell me a joke", "Read me the news", "Battery status",
                  "Volume up", "Volume down", "Play some music"]
STATE_NAMES = {"idle": "Ready", "listening": "Listening",
               "thinking": "Working", "speaking": "Speaking",
               "muted": "Muted"}
QUOTES = [
    "Wakanda forever.", "Avengers, assemble.", "Whatever it takes.",
    "I can do this all day.", "With great power comes great responsibility.",
    "Heroes are made by the paths they choose.",
    "Part of the journey is the end.", "Higher, further, faster.",
    "The world is changing. Be ready.", "Suit up. Today needs you."]



LOADOUTS = [   # name, tagline, emblem word, settings it applies
    ("Armored Genius", "Red-and-gold power, dry wit.", "iron",
     {"theme": "Ember", "voice_style": "jarvis", "orbit_count": 4,
      "orbit_speed": 1.3, "wave_style": "both", "mode": "sarcastic"}),
    ("First Avenger", "Steady, loyal, star-spangled.", "captain america",
     {"theme": DEFAULT_THEME, "voice_style": "commander",
      "orbit_count": 3, "orbit_speed": 1.0, "wave_style": "ring",
      "mode": "serious"}),
    ("God of Thunder", "Booming and electric.", "thor",
     {"theme": "Arctic", "voice_style": "titan", "orbit_count": 5,
      "orbit_speed": 1.6, "wave_style": "bars", "mode": "normal"}),
    ("Green Rage", "Loud. Very loud.", "hulk",
     {"theme": "Emerald", "voice_style": "overlord", "orbit_count": 2,
      "orbit_speed": 2.0, "wave_style": "both", "mode": "normal"}),
    ("Quiet Operative", "Sharp, calm, mission-focused.", "widow",
     {"theme": "Midnight Silver", "voice_style": "agent", "orbit_count": 2,
      "orbit_speed": 0.7, "wave_style": "ring", "mode": "serious"}),
    ("Mystic Arts", "Calm, golden, a little magical.", "strange",
     {"theme": "Platinum Gold", "voice_style": "sage", "orbit_count": 6,
      "orbit_speed": 0.9, "wave_style": "ring", "mode": "friendly"}),
    ("Sharpshooter", "Precise. Never misses a command.", "hawk",
     {"theme": DEFAULT_THEME, "voice_style": "cadet", "orbit_count": 3,
      "orbit_speed": 1.2, "wave_style": "bars", "mode": "friendly"}),
    ("Cosmic Captain", "Bright, bold, unstoppable.", "captain marvel",
     {"theme": "Ember", "voice_style": "nova", "orbit_count": 5,
      "orbit_speed": 1.4, "wave_style": "both", "mode": "friendly"}),
]


def typed_to_command(text):
    """Turn typed text into the same form a spoken command arrives in."""
    words = re.sub(r"[^\w\s]", " ", text.lower()).split()
    i = find_wake_word(words)
    if i != -1:
        words = words[:i] + words[i + 1:]
    return " ".join(words)


def refresh_tray_icon():
    """Redraw the tray icon so it matches the logo you picked."""
    icon = tray_ref.get("icon")
    if icon is None:
        return
    try:
        tray_ref["on"] = make_tray_image(False)
        tray_ref["off"] = make_tray_image(True)
        icon.icon = tray_ref["off"] if state["muted"] else tray_ref["on"]
    except Exception as error:
        print("Tray icon refresh failed:", error)


class DragBar(tk.Canvas):
    """A wide scroll bar you can grab and drag, or click to jump."""

    def __init__(self, parent, target):
        tk.Canvas.__init__(self, parent, width=14, bg=PANEL_BG,
                           highlightthickness=0, cursor=hand_cursor())
        self.target = target
        self.first, self.last = 0.0, 1.0
        self.grab = None
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<ButtonPress-1>", self.press)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", lambda e: self.release())
        self.bind("<Enter>", lambda e: self.draw(True))
        self.bind("<Leave>", lambda e: self.draw(False))
        self.hot = False

    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self.draw()

    def thumb(self):
        height = max(1, self.winfo_height())
        top = self.first * height
        bottom = max(top + 36, self.last * height)
        return top, min(height, bottom), height

    def draw(self, hot=None):
        if hot is not None:
            self.hot = hot
        self.delete("all")
        top, bottom, height = self.thumb()
        self.create_rectangle(5, 0, 9, height, fill=PANEL_CARD2, outline="")
        if self.last - self.first < 0.999:
            color = PANEL_VIOLET if (self.hot or self.grab is not None) \
                else PANEL_GOLD
            self.create_rectangle(2, top, 12, bottom, fill=color, outline="")

    def press(self, event):
        top, bottom, height = self.thumb()
        if top <= event.y <= bottom:
            self.grab = event.y - top
        else:
            self.grab = (bottom - top) / 2.0
            self.drag(event)
        self.draw()

    def drag(self, event):
        if self.grab is None:
            return
        top, bottom, height = self.thumb()
        span = max(1.0, height - (bottom - top))
        pos = (event.y - self.grab) / span
        shown = self.last - self.first
        self.target.yview_moveto(max(0.0, min(1.0 - shown, pos * (1.0 - shown))))

    def release(self):
        self.grab = None
        self.draw()


class ControlPanel:
    """Optimus control panel: red and blue, with every setting in one place."""
    NAV = [("command", "Console"), ("logos", "Emblems"),
           ("anim", "Orb"), ("cursor", "Cursor"),
           ("voice", "Voice"), ("keys", "Hotkeys"),
           ("loadout", "Presets"), ("system", "Settings")]
    COLUMNS = 4

    def __init__(self, root):
        from tkinter import ttk
        apply_panel_theme()
        refresh_cursor_look()
        self.win = tk.Toplevel(root)
        self.win.title("Optimus - Control Panel")
        self.win.geometry("1040x740")
        self.win.minsize(900, 620)
        self.win.configure(bg=PANEL_BG)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.thumbs = []
        self.cards = {}
        self.history = []
        self.hist_pos = 0
        self.feed = queue.Queue()
        self.speak = tk.BooleanVar(master=self.win, value=True)
        self.status = tk.StringVar(master=self.win, value="")
        self.pages = {}
        self.nav_items = {}
        self.current = None
        self.scrollers = {}
        self.active_canvas = None
        self.badge = None
        self.tick = 0
        self.ui_calls = queue.Queue()

        style = ttk.Style(self.win)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Vertical.TScrollbar", background=PANEL_EDGE,
                        troughcolor=PANEL_BG, bordercolor=PANEL_BG,
                        arrowcolor=PANEL_DIM, lightcolor=PANEL_EDGE,
                        darkcolor=PANEL_EDGE)
        style.map("Vertical.TScrollbar",
                  background=[("active", PANEL_BLUE)])
        self.set_window_icon()

        # header: name on the left, the quote in the middle, status right
        self.header = tk.Canvas(self.win, height=64, bg=PANEL_BG,
                                highlightthickness=0)
        self.header.pack(fill="x")
        self.header.create_text(28, 32, text="OPTIMUS", anchor="w",
                                fill=PANEL_TEXT, font=(PANEL_FONT, 20, "bold"))
        self.quote_text = self.header.create_text(
            500, 32, text="", anchor="center", fill=PANEL_DIM, justify="center",
            font=(PANEL_FONT, 11, "italic"))
        self.quote_index = random.randrange(len(QUOTES))
        self.header.bind("<Button-1>", lambda e: self.next_quote())
        self.header.create_line(0, 63, 4000, 63, fill=PANEL_EDGE, tags="hair")
        self.flash = 0.0
        self.stone_ids = []
        self.state_dot = self.header.create_oval(0, 0, 0, 0, fill=PANEL_VIOLET,
                                                 outline="")
        self.state_text = self.header.create_text(0, 0, text="", anchor="e",
                                                  fill=PANEL_TEXT,
                                                  font=(PANEL_FONT, 10,
                                                        "bold"))
        self.header.bind("<Configure>", self.place_state)

        body = tk.Frame(self.win, bg=PANEL_BG)
        body.pack(fill="both", expand=True)
        self.side = tk.Frame(body, bg=PANEL_SIDE, width=214)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)
        self.content = tk.Frame(body, bg=PANEL_BG)
        self.content.pack(side="left", fill="both", expand=True, padx=(18, 8))

        self.build_sidebar()
        for key, _ in self.NAV:
            page = tk.Frame(self.content, bg=PANEL_BG)
            self.pages[key] = page
        self.build_chat(self.pages["command"])
        self.build_logos(self.pages["logos"])
        self.builders = {"anim": self.build_anim, "cursor": self.build_cursor,
                         "voice": self.build_voice, "keys": self.build_keys,
                         "loadout": self.build_loadout,
                         "system": self.build_system}
        for key, builder in self.builders.items():
            builder(self.scroll_page(self.pages[key], key))

        tk.Label(self.win, textvariable=self.status, bg=PANEL_SIDE,
                 fg=PANEL_DIM, font=(PANEL_FONT, 10), anchor="w",
                 padx=18, pady=6).pack(fill="x", side="bottom")
        self.win.bind_all("<MouseWheel>", self.on_wheel)

        for kind, text in list(chat_history):
            self.add_line(kind, text)
        chat_listeners.append(self.feed)
        self.show("command")
        apply_cursor_look(self.win)
        self.win.after(150, self.poll)
        self.win.after(40, self.animate)
        self.raise_window()

    # ---- look helpers ----
    def set_window_icon(self):
        try:
            from PIL import Image, ImageTk
            logo = prepare_logo(current_logo_path()).convert("RGBA").resize(
                (64, 64), Image.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(logo)
            self.win.iconphoto(False, self.icon_photo)
        except Exception:
            pass

    def make_header_image(self):
        return None

    def place_state(self, event=None):
        width = max(700, self.header.winfo_width())
        self.header.coords(self.state_dot, width - 130, 28, width - 122, 36)
        self.header.coords(self.state_text, width - 28, 32)
        self.header.coords("hair", 0, 63, width, 63)
        self.header.coords(self.quote_text, width / 2.0, 32)
        self.header.itemconfigure(self.quote_text, width=max(220, width - 520))

    def tween(self, widget, props):
        """Fade a widget's colours when the mouse moves on or off it.
        props: {"bg": (normal, hover), "fg": (normal, hover)}"""
        info = {"t": 0.0, "goal": 0.0, "job": None}

        def step():
            info["job"] = None
            try:
                diff = info["goal"] - info["t"]
                info["t"] = (info["goal"] if abs(diff) < 0.06
                             else info["t"] + diff * 0.5)
                for option, (off, on) in props.items():
                    widget.configure(**{option: mix_color(off, on, info["t"])})
                if info["t"] != info["goal"]:
                    info["job"] = widget.after(16, step)
            except tk.TclError:
                pass

        def go(goal):
            info["goal"] = goal
            if info["job"] is None:
                step()

        widget.bind("<Enter>", lambda e: go(1.0), add="+")
        widget.bind("<Leave>", lambda e: go(0.0), add="+")
        widget._tween_go = go

    def button(self, parent, text, command, kind="ghost", padx=16):
        filled = kind == "red"
        base = PANEL_GOLD if filled else PANEL_CARD
        hover = PANEL_VIOLET if filled else mix_color(PANEL_CARD, PANEL_GOLD,
                                                      0.35)
        label = tk.Label(parent, text=text, bg=base,
                         fg="#ffffff" if filled else PANEL_VIOLET,
                         font=(PANEL_FONT, 10, "bold"), padx=padx, pady=7,
                         cursor=hand_cursor(), highlightthickness=1,
                         highlightbackground=PANEL_GOLD if kind != "ghost"
                         else PANEL_EDGE)
        self.tween(label, {"bg": (base, hover)})

        def pressed(event):
            label.configure(bg="#ffffff", fg="#000000")
            label.after(90, lambda: label.configure(
                bg=hover, fg="#ffffff" if filled else PANEL_VIOLET))
            command()

        label.bind("<Button-1>", pressed)
        return label

    def card(self, parent, title, note=None, accent=None):
        outer = tk.Frame(parent, bg=PANEL_CARD, highlightthickness=1,
                         highlightbackground=PANEL_EDGE)
        outer.pack(fill="x", pady=(0, 12), padx=(0, 6))
        inner = tk.Frame(outer, bg=PANEL_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(inner, text=title.upper(), bg=PANEL_CARD, fg=PANEL_VIOLET,
                 font=(PANEL_FONT, 9, "bold")).pack(anchor="w")
        if note:
            tk.Label(inner, text=note, bg=PANEL_CARD, fg=PANEL_DIM,
                     font=(PANEL_FONT, 9), wraplength=680,
                     justify="left").pack(anchor="w", pady=(3, 0))
        body = tk.Frame(inner, bg=PANEL_CARD)
        body.pack(fill="x", pady=(12, 0))
        return body

    def chips(self, parent, options, current, on_pick, columns=6):
        holder = tk.Frame(parent, bg=PANEL_CARD)
        labels = {}

        def paint():
            for name, lab in labels.items():
                on = name == self.chip_value[id(holder)]
                lab.configure(bg=PANEL_GOLD if on else PANEL_CARD,
                              fg="#ffffff" if on else PANEL_DIM,
                              highlightbackground=PANEL_GOLD if on
                              else PANEL_EDGE)

        if not hasattr(self, "chip_value"):
            self.chip_value = {}
        self.chip_value[id(holder)] = current
        for i, name in enumerate(options):
            lab = tk.Label(holder, text=str(name).title()
                           if str(name).islower() else str(name),
                           bg=PANEL_CARD, fg=PANEL_DIM, cursor=hand_cursor(),
                           font=(PANEL_FONT, 10), padx=13, pady=5,
                           highlightthickness=1,
                           highlightbackground=PANEL_EDGE)
            lab.grid(row=i // columns, column=i % columns, padx=(0, 6),
                     pady=(0, 6), sticky="w")

            def picked(event, n=name):
                self.chip_value[id(holder)] = n
                paint()
                on_pick(n)

            lab.bind("<Button-1>", picked)
            lab.bind("<Enter>", lambda e, l=lab, n=name: l.configure(
                bg=PANEL_GOLD if n == self.chip_value[id(holder)]
                else PANEL_CARD2))
            lab.bind("<Leave>", lambda e: paint())
            labels[name] = lab
        paint()
        return holder

    def switch(self, parent, text, value, on_change):
        row = tk.Frame(parent, bg=PANEL_CARD)
        tk.Label(row, text=text, bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11), width=30, anchor="w").pack(
                     side="left")
        cv = tk.Canvas(row, width=48, height=26, bg=PANEL_CARD,
                       highlightthickness=0, cursor=hand_cursor())
        cv.pack(side="left")
        info = {"on": bool(value), "x": 1.0 if value else 0.0, "job": None}

        def draw():
            cv.delete("all")
            col = mix_color(PANEL_EDGE, PANEL_BLUE, info["x"])
            cv.create_oval(1, 1, 25, 25, fill=col, outline="")
            cv.create_oval(23, 1, 47, 25, fill=col, outline="")
            cv.create_rectangle(13, 1, 35, 25, fill=col, outline="")
            kx = 13 + info["x"] * 22
            cv.create_oval(kx - 10, 3, kx + 10, 23, fill="#ffffff",
                           outline="")

        def step():
            info["job"] = None
            goal = 1.0 if info["on"] else 0.0
            diff = goal - info["x"]
            info["x"] = goal if abs(diff) < 0.08 else info["x"] + diff * 0.5
            draw()
            if info["x"] != goal:
                info["job"] = cv.after(16, step)

        def flip(event=None):
            info["on"] = not info["on"]
            on_change(info["on"])
            if info["job"] is None:
                step()

        cv.bind("<Button-1>", flip)
        draw()
        return row

    def slider(self, parent, text, low, high, value, on_release, step=1,
               unit=""):
        row = tk.Frame(parent, bg=PANEL_CARD)
        tk.Label(row, text=text, bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11), width=22, anchor="w").pack(
                     side="left")
        track = 300
        cv = tk.Canvas(row, width=track + 24, height=30, bg=PANEL_CARD,
                       highlightthickness=0, cursor=hand_cursor())
        cv.pack(side="left")
        readout = tk.Label(row, text="", bg=PANEL_CARD, fg=PANEL_TEXT,
                           font=(PANEL_FONT, 10, "bold"), width=8,
                           anchor="w")
        readout.pack(side="left", padx=(8, 0))
        info = {"v": max(low, min(high, value))}

        def snap(v):
            v = round((v - low) / float(step)) * step + low
            return max(low, min(high, v))

        def draw():
            cv.delete("all")
            frac = (info["v"] - low) / float(high - low)
            x = 12 + frac * track
            cv.create_line(12, 15, 12 + track, 15, fill=PANEL_CARD2,
                           width=6, capstyle="round")
            cv.create_line(12, 15, x, 15, fill=PANEL_RED, width=6,
                           capstyle="round")
            cv.create_oval(x - 9, 6, x + 9, 24, fill="#ffffff",
                           outline=PANEL_BLUE, width=3)
            shown = int(info["v"]) if float(step).is_integer() else info["v"]
            readout.configure(text="%s%s" % (shown, " " + unit if unit
                                             else ""))

        def move(event):
            frac = (event.x - 12) / float(track)
            info["v"] = snap(low + max(0.0, min(1.0, frac)) * (high - low))
            draw()

        cv.bind("<Button-1>", move)
        cv.bind("<B1-Motion>", move)
        cv.bind("<ButtonRelease-1>", lambda e: on_release(info["v"]))
        draw()
        return row

    def menu(self, parent, variable, choices, command, width=12):
        widget = tk.OptionMenu(parent, variable, *choices, command=command)
        widget.config(bg=PANEL_CARD2, fg=PANEL_TEXT, relief="flat",
                      activebackground=PANEL_EDGE, activeforeground="#ffffff",
                      highlightthickness=0, font=(PANEL_FONT, 10),
                      width=width, bd=0, cursor=hand_cursor())
        widget["menu"].config(bg=PANEL_CARD2, fg=PANEL_TEXT,
                              activebackground=PANEL_GOLD,
                              activeforeground=PANEL_INK,
                              font=(PANEL_FONT, 10))
        return widget

    def entry(self, parent, width=30):
        return tk.Entry(parent, bg=PANEL_CARD2, fg=PANEL_TEXT,
                        insertbackground=PANEL_BLUE, relief="flat",
                        font=(PANEL_FONT, 11), highlightthickness=1,
                        highlightbackground=PANEL_EDGE,
                        highlightcolor=PANEL_RED, width=width)

    # ---- sidebar and pages ----
    def build_sidebar(self):
        self.badge_canvas = tk.Canvas(self.side, width=214, height=150,
                                      bg=PANEL_SIDE, highlightthickness=0)
        self.badge_canvas.pack()
        self.badge_canvas.configure(cursor=hand_cursor())
        self.badge_canvas.bind("<Button-1>", lambda e: self.cycle_logo())
        self.spin = 0.0
        self.load_badge()
        for key, label in self.NAV:
            row = tk.Frame(self.side, bg=PANEL_SIDE, cursor=hand_cursor())
            row.pack(fill="x", pady=1)
            strip = tk.Frame(row, bg=PANEL_SIDE, width=5)
            strip.pack(side="left", fill="y")
            text = tk.Label(row, text=label, bg=PANEL_SIDE, fg=PANEL_DIM,
                            font=(PANEL_FONT, 11), anchor="w",
                            padx=20, pady=10, cursor=hand_cursor())
            text.pack(side="left", fill="x", expand=True)
            self.tween(text, {"fg": (PANEL_DIM, PANEL_TEXT)})
            for widget in (row, text, strip):
                widget.bind("<Button-1>", lambda e, k=key: self.show(k),
                            add="+")
            self.nav_items[key] = (row, strip, text)
        tk.Label(self.side, text="A V E N G E R S   I N I T I A T I V E",
                 bg=PANEL_SIDE, fg=PANEL_VIOLET, font=(PANEL_FONT, 7, "bold")
                 ).pack(side="bottom", pady=(0, 12))
        tk.Label(self.side, text="Say \"Optimus\", or hold your talk key.",
                 bg=PANEL_SIDE, fg=PANEL_DIM, font=(PANEL_FONT, 9),
                 wraplength=180).pack(side="bottom", pady=(0, 14))
        self.button(self.side, "Assemble", self.assemble, kind="red",
                    padx=44).pack(side="bottom", pady=(0, 14))

    def load_badge(self):
        try:
            from PIL import Image, ImageTk
            logo = prepare_logo(current_logo_path()).convert("RGBA").resize(
                (96, 96), Image.LANCZOS)
            self.badge = ImageTk.PhotoImage(logo)
        except Exception:
            self.badge = None

    def show(self, key):
        for name, page in self.pages.items():
            page.place_forget()
        page = self.pages[key]
        page.place(x=36, y=16, relwidth=1.0, relheight=1.0, height=-24)
        self.slide(page, 36 if settings.get("page_slide", True) else 0)
        self.current = key
        self.active_canvas = self.scrollers.get(key)
        for name, (row, strip, text) in self.nav_items.items():
            on = name == key
            row.configure(bg=PANEL_CARD if on else PANEL_SIDE)
            text.configure(bg=PANEL_CARD if on else PANEL_SIDE)
            index = [k for k, _ in self.NAV].index(name)
            strip.configure(bg=PANEL_GOLD if on else PANEL_SIDE)
            if on:
                text.configure(fg=PANEL_TEXT)
        if key == "command":
            try:
                self.entry_box.focus_set()
            except Exception:
                pass

    def slide(self, page, offset):
        """Pages glide in from the right."""
        try:
            if offset <= 1:
                page.place_configure(x=0)
                return
            page.place_configure(x=int(offset))
            page.after(14, lambda: self.slide(page, offset * 0.62))
        except tk.TclError:
            pass

    def next_quote(self):
        self.quote_index = (self.quote_index + 1) % len(QUOTES)
        self.header.itemconfigure(self.quote_text,
                                  text="\u201c%s\u201d" % QUOTES[self.quote_index])

    def cycle_logo(self):
        items = list_logos()
        if not items:
            return
        current = settings.get("logo_file") or ORB_IMAGE
        paths = [rel for label, rel in items]
        index = (paths.index(current) + 1) % len(paths) if current in paths \
            else 0
        self.spin = 1.0
        self.apply_logo(paths[index], items[index][0])

    def assemble(self):
        """Avengers, assemble: a full-screen Marvel scene plus a line."""
        orb_state["demo_until"] = time.time() + 4.0
        self.flash = 1.0
        self.next_quote()
        line = QUOTES[self.quote_index]
        choice = settings.get("screen_fx", "Random")
        orb_cmds.put(("assemble", None if choice == "Random" else choice))
        self.status.set("Assembling... " + line)
        say(line)

    def scroll_page(self, page, key):
        canvas = tk.Canvas(page, bg=PANEL_BG, highlightthickness=0,
                           yscrollincrement=36)
        bar = DragBar(page, canvas)
        bar.pack(side="right", fill="y", padx=(4, 0))
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=PANEL_BG)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            window, width=e.width))
        self.scrollers[key] = canvas
        return inner

    def fix_scroll(self):
        """Re-measure every page (after tabs switch) and go back to the top."""
        for canvas in self.scrollers.values():
            try:
                canvas.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.yview_moveto(0)
            except tk.TclError:
                pass

    def page_of(self, widget):
        """Which page (and its scroll canvas) a widget lives on."""
        node = widget
        while node is not None and not isinstance(node, str):
            for key, page in self.pages.items():
                if node is page:
                    return key
            node = getattr(node, "master", None)
        return None

    def on_wheel(self, event):
        """Mouse wheel and trackpad scrolling for the page under the pointer.

        Windows sends wheel events to whichever widget has keyboard focus, not
        the one under the pointer, so we look at where the pointer really is."""
        try:
            px, py = self.win.winfo_pointerxy()
        except Exception:
            px, py = event.x_root, event.y_root
        try:
            left, top = self.win.winfo_rootx(), self.win.winfo_rooty()
            if not (left <= px <= left + self.win.winfo_width()
                    and top <= py <= top + self.win.winfo_height()):
                return                      # pointer is over another window
        except Exception:
            pass
        key = None
        try:
            key = self.page_of(self.win.winfo_containing(px, py))
        except Exception:
            key = None
        if key is None:
            key = self.current
        try:
            self.wheel_acc = getattr(self, "wheel_acc", 0.0) - event.delta / 120.0
            steps = int(self.wheel_acc)
            if not steps:
                return
            self.wheel_acc -= steps
            if key == "command":
                self.log.yview_scroll(steps * 3, "units")
                return
            canvas = self.scrollers.get(key)
            if canvas is not None:
                canvas.yview_scroll(steps * 2, "units")
        except Exception:
            pass

    # ---- window helpers ----
    def alive(self):
        try:
            return bool(self.win.winfo_exists())
        except Exception:
            return False

    def raise_window(self):
        try:
            self.win.deiconify()
            self.win.lift()
            self.win.attributes("-topmost", True)
            self.win.after(400, lambda: self.win.attributes("-topmost", False))
            self.win.focus_force()
            if self.current == "command":
                self.entry_box.focus_set()
        except Exception:
            pass

    def close(self):
        try:
            chat_listeners.remove(self.feed)
        except ValueError:
            pass
        try:
            self.win.unbind_all("<MouseWheel>")
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass

    def animate(self):
        """A thin ring on the badge and a soft shimmer on the header line."""
        if not self.alive():
            return
        self.tick += 1
        now = time.time()
        try:
            c = self.badge_canvas
            c.delete("all")
            cx, cy = 107, 76
            muted = state["muted"]
            col = PANEL_EDGE if muted else PANEL_GOLD
            self.spin = max(0.0, self.spin - 0.04)
            boost = now * 40 + self.spin * self.spin * 360
            c.create_oval(cx - 58, cy - 58, cx + 58, cy + 58,
                          outline=PANEL_EDGE, width=1)
            c.create_arc(cx - 58, cy - 58, cx + 58, cy + 58,
                         start=boost % 360, extent=70, style="arc",
                         outline=col, width=2)
            c.create_arc(cx - 58, cy - 58, cx + 58, cy + 58,
                         start=(boost + 180) % 360, extent=30, style="arc",
                         outline=PANEL_VIOLET if not muted else PANEL_EDGE,
                         width=2)
            if self.flash > 0:
                self.flash = max(0.0, self.flash - 0.03)
                ring = 58 + (1 - self.flash) * 40
                c.create_oval(cx - ring, cy - ring, cx + ring, cy + ring,
                              outline=mix_color(PANEL_SIDE, PANEL_VIOLET,
                                                self.flash), width=2)
            if self.badge is not None:
                c.create_image(cx, cy, image=self.badge)
            h = self.header
            h.delete("sweep")
            if settings.get("header_shimmer", True):
                width = max(400, h.winfo_width())
                pos = (now * 220) % (width + 300) - 150
                for i in range(0, 300, 6):
                    x = pos + i
                    if 0 <= x <= width:
                        fade = 1 - abs(i - 150) / 150.0
                        h.create_line(x, 63, x + 6, 63, width=2, tags="sweep",
                                      fill=mix_color(PANEL_EDGE, PANEL_VIOLET,
                                                     fade))
            if self.tick == 1:
                self.next_quote()
            if self.tick % 480 == 0:
                self.next_quote()
            if self.tick % 8 == 0:
                mode = "muted" if state["muted"] else orb_state.get("mode",
                                                                    "idle")
                h.itemconfigure(self.state_text,
                                text=STATE_NAMES.get(mode, "Ready"))
                box = h.bbox(self.state_text)
                if box:
                    h.coords(self.state_dot, box[0] - 16, 28, box[0] - 8, 36)
                h.itemconfigure(self.state_dot, fill=PANEL_DIM if mode ==
                                "muted" else PANEL_VIOLET)
        except tk.TclError:
            return
        self.win.after(40, self.animate)

    # ---- page: type a command ----
    def build_chat(self, parent):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill="x", pady=(4, 6), side="bottom")
        self.entry_box = self.entry(row)
        self.entry_box.configure(font=(PANEL_FONT, 12))
        self.entry_box.pack(side="left", fill="x", expand=True, ipady=9,
                            padx=(0, 8))
        self.entry_box.bind("<Return>", lambda e: self.send())
        self.entry_box.bind("<Up>", lambda e: self.recall(-1))
        self.entry_box.bind("<Down>", lambda e: self.recall(1))
        self.button(row, "Send", self.send, kind="red", padx=22).pack(
            side="left")
        tk.Checkbutton(row, text="Speak the reply", variable=self.speak,
                       bg=PANEL_BG, fg=PANEL_TEXT, selectcolor=PANEL_CARD2,
                       activebackground=PANEL_BG, activeforeground=PANEL_TEXT,
                       font=(PANEL_FONT, 10)).pack(side="left", padx=(12, 0))

        chips = tk.Frame(parent, bg=PANEL_BG)
        chips.pack(fill="x", pady=(0, 6), side="bottom")
        for i, text in enumerate(QUICK_COMMANDS):
            self.button(chips, text, lambda t=text: self.send(t),
                        padx=12).grid(row=i // 4, column=i % 4,
                                      padx=(0, 6), pady=(0, 6), sticky="w")

        box = tk.Frame(parent, bg=PANEL_CARD)
        box.pack(fill="both", expand=True, pady=(0, 10))
        self.log = tk.Text(box, bg=PANEL_CARD, fg=PANEL_TEXT, wrap="word",
                           relief="flat", font=(PANEL_FONT, 11), padx=16,
                           pady=14, state="disabled", cursor=arrow_cursor(),
                           highlightthickness=0, spacing3=2)
        from tkinter import ttk
        bar = ttk.Scrollbar(box, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.tag_configure("who", foreground=PANEL_DIM,
                               font=(PANEL_FONT, 9, "bold"))
        self.log.tag_configure("you", foreground="#8fc3ff",
                               font=(PANEL_FONT, 11, "bold"))
        self.log.tag_configure("voice", foreground=PANEL_DIM,
                               font=(PANEL_FONT, 11, "italic"))
        self.log.tag_configure("optimus", foreground=PANEL_TEXT)
        self.log.tag_configure("optname", foreground=PANEL_RED,
                               font=(PANEL_FONT, 9, "bold"))
        self.add_text("Type a command below, exactly as you would say it. "
                      "Optimus runs it the same way as your voice.\n\n",
                      "voice")

    def add_text(self, text, tag):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag)
        self.log.configure(state="disabled")
        self.log.see("end")

    def add_line(self, kind, text):
        label, tag, wtag = {"typed": ("YOU", "you", "who"),
                            "heard": ("YOU (VOICE)", "voice", "who"),
                            "Optimus": ("OPTIMUS", "optimus",
                                        "optname")}.get(kind,
                                                        (None, None, None))
        if label:
            self.add_text(label + "\n", wtag)
            self.add_text(text + "\n\n", tag)

    def send(self, text=None):
        text = (text if text is not None else self.entry_box.get()).strip()
        if not text:
            return
        self.entry_box.delete(0, "end")
        self.history.append(text)
        self.hist_pos = len(self.history)
        log_event("typed", text)
        typed_queue.put((text, bool(self.speak.get())))
        self.status.set("Sent. Optimus is working on it...")

    def recall(self, step):
        if self.history:
            self.hist_pos = max(0, min(len(self.history),
                                       self.hist_pos + step))
            self.entry_box.delete(0, "end")
            if self.hist_pos < len(self.history):
                self.entry_box.insert(0, self.history[self.hist_pos])
        return "break"

    def poll(self):
        if not self.alive():
            return
        try:
            while True:
                kind, text = self.feed.get_nowait()
                self.add_line(kind, text)
                if kind == "Optimus":
                    self.status.set("")
        except queue.Empty:
            pass
        try:
            while True:
                self.ui_calls.get_nowait()()
        except queue.Empty:
            pass
        self.win.after(150, self.poll)

    # ---- page: logos ----
    def build_logos(self, parent):
        top = tk.Frame(parent, bg=PANEL_BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Choose your emblem. It becomes your orb, tray icon and "
                 "desktop icon instantly.", bg=PANEL_BG, fg=PANEL_DIM,
                 font=(PANEL_FONT, 10)).pack(side="left")
        buttons = tk.Frame(parent, bg=PANEL_BG)
        buttons.pack(side="bottom", fill="x", pady=(10, 0))
        self.button(buttons, "Add my own logos...", self.add_own,
                    kind="red").pack(side="left")
        self.button(buttons, "Import a logo sheet...", self.import_sheet,
                    kind="blue").pack(side="left", padx=8)
        self.button(buttons, "Open logos folder", self.open_folder).pack(
            side="left")
        holder = tk.Frame(parent, bg=PANEL_BG)
        holder.pack(fill="both", expand=True)
        self.grid_frame = self.scroll_page(holder, "logos")
        self.fill_logos()

    def fill_logos(self):
        from PIL import Image, ImageTk
        ensure_logo_pack()
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.thumbs.clear()
        self.cards.clear()
        for index, (label, rel) in enumerate(list_logos()):
            card = tk.Frame(self.grid_frame, bg=PANEL_CARD, cursor=hand_cursor(),
                            highlightthickness=2,
                            highlightbackground=PANEL_EDGE)
            card.grid(row=index // self.COLUMNS, column=index % self.COLUMNS,
                      padx=7, pady=7)
            photo = None
            try:
                logo = prepare_logo(os.path.join(BASE_DIR, rel)).convert(
                    "RGBA").resize((92, 92), Image.LANCZOS)
                tile = Image.new("RGBA", (92, 92), PANEL_CARD)
                tile.alpha_composite(logo)
                photo = ImageTk.PhotoImage(tile)
                self.thumbs.append(photo)
            except Exception as error:
                print("Logo preview failed for %s: %s" % (rel, error))
            if photo is not None:
                picture = tk.Label(card, image=photo, bg=PANEL_CARD)
            else:
                picture = tk.Label(card, text="?", bg=PANEL_CARD,
                                   fg=PANEL_DIM, width=10, height=5)
            name = tk.Label(card, text=label, bg=PANEL_CARD, fg=PANEL_TEXT,
                            font=(PANEL_FONT, 10, "bold"))
            picture.pack(padx=18, pady=(12, 4))
            name.pack(pady=(0, 10))
            for widget in (card, picture, name):
                widget.bind("<Button-1>",
                            lambda e, r=rel, l=label: self.apply_logo(r, l))
                widget.bind("<Enter>", lambda e, r=rel: self.hover_card(r, 1))
                widget.bind("<Leave>", lambda e, r=rel: self.hover_card(r, 0))
            self.cards[rel] = card
        self.highlight()
        apply_cursor_look(self.grid_frame)

    def hover_card(self, rel, on):
        card = self.cards.get(rel)
        if card is None:
            return
        current = settings.get("logo_file") or ORB_IMAGE
        if rel == current:
            return
        card.configure(highlightbackground=PANEL_BLUE if on else PANEL_EDGE)

    def highlight(self):
        current = settings.get("logo_file") or ORB_IMAGE
        known = set(self.cards)
        if current not in known and self.cards:
            current = list(self.cards)[0]
        for rel, card in self.cards.items():
            card.configure(highlightbackground=PANEL_RED if rel == current
                           else PANEL_EDGE)

    def apply_logo(self, rel, label):
        save_setting("logo_file", rel)
        orb_cmds.put(("logo",))
        threading.Thread(target=refresh_tray_icon, daemon=True).start()
        self.load_badge()
        self.set_window_icon()
        self.highlight()
        if not settings.get("cursor_emblem"):
            self.rebuild_pointer()
        self.status.set("Emblem changed to %s." % label)

    def add_own(self):
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            parent=self.win, title="Choose your logo images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("All files", "*.*")])
        if not paths:
            return
        added = []
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            for path in paths:
                stem, ext = os.path.splitext(os.path.basename(path))
                fname = "my_%s%s" % (re.sub(r"[^\w\-]+", "_", stem),
                                     ext.lower())
                shutil.copy2(path, os.path.join(LOGO_DIR, fname))
                added.append(("logos/" + fname,
                              stem.replace("_", " ").strip().title()))
            self.fill_logos()
            self.apply_logo(*added[-1])
            self.status.set("Added %d logo%s." % (
                len(added), "" if len(added) == 1 else "s"))
        except Exception as error:
            self.status.set("Couldn't add that image: %s" % error)

    def import_sheet(self):
        """Pick one picture holding many logos; each becomes its own logo."""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.win, title="Choose the picture with all your logos",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("All files", "*.*")])
        if not path:
            return
        self.status.set("Cutting the sheet into separate logos...")

        def work():
            try:
                found = split_logo_sheet(path)
                message = "Imported %d logos." % len(found)
            except Exception as error:
                found = []
                message = "Couldn't read that picture: %s" % error

            def done():
                self.status.set(message)
                if found:
                    self.fill_logos()
                    self.refresh_page("cursor")
                    self.apply_logo(*found[0])

            self.ui_calls.put(done)

        threading.Thread(target=work, daemon=True).start()

    def open_folder(self):
        try:
            os.makedirs(LOGO_DIR, exist_ok=True)
            os.startfile(LOGO_DIR)
        except Exception as error:
            self.status.set("Couldn't open the folder: %s" % error)

    # ---- page: animations ----
    def color_swatch(self, parent, text, key, default, after=None):
        """A row with a coloured square; click it to choose any colour."""
        row = tk.Frame(parent, bg=PANEL_CARD)
        tk.Label(row, text=text, bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11), width=22, anchor="w").pack(side="left")
        box = tk.Label(row, width=6, bg=settings.get(key) or default,
                       cursor=hand_cursor(), relief="flat")
        box.pack(side="left", ipady=4)
        code = tk.Label(row, text=(settings.get(key) or default).upper(),
                        bg=PANEL_CARD, fg=PANEL_DIM, font=(PANEL_FONT, 10))
        code.pack(side="left", padx=10)

        def choose(event=None):
            from tkinter import colorchooser
            picked = colorchooser.askcolor(color=box.cget("bg"),
                                           parent=self.win, title=text)
            if picked and picked[1]:
                box.configure(bg=picked[1])
                code.configure(text=picked[1].upper())
                save_setting(key, picked[1])
                if after:
                    after()
                self.status.set("%s: %s" % (text, picked[1].upper()))

        def clear(event=None):
            settings.pop(key, None)
            save_setting("_touch", time.time())
            box.configure(bg=default)
            code.configure(text=default.upper())

        box.bind("<Button-1>", choose)
        reset = tk.Label(row, text="reset", bg=PANEL_CARD, fg=PANEL_DIM,
                         font=(PANEL_FONT, 9, "underline"),
                         cursor=hand_cursor())
        reset.pack(side="left")
        reset.bind("<Button-1>", clear)
        return row

    def mode_color(self, mode, default):
        def choose(event=None):
            from tkinter import colorchooser
            picked = colorchooser.askcolor(color=default, parent=self.win,
                                           title=mode.title())
            if picked and picked[1]:
                colors = dict(settings.get("mode_colors") or {})
                colors[mode] = picked[1]
                save_setting("mode_colors", colors)
                self.status.set("%s colour: %s" % (mode.title(), picked[1]))
        return choose

    def subtabs(self, page, names):
        """Quiet text tabs across the top of a page; returns one frame per tab."""
        bar = tk.Frame(page, bg=PANEL_BG)
        bar.pack(fill="x", pady=(0, 14))
        area = tk.Frame(page, bg=PANEL_BG)
        area.pack(fill="x")
        frames, labels = {}, {}
        for name in names:
            frames[name] = tk.Frame(area, bg=PANEL_BG)
            lab = tk.Label(bar, text=name, bg=PANEL_BG, fg=PANEL_DIM,
                           font=(PANEL_FONT, 11), padx=14, pady=6,
                           cursor=hand_cursor())
            lab.pack(side="left")
            labels[name] = lab

            def go(event=None, n=name):
                for k, f in frames.items():
                    f.pack_forget()
                    labels[k].configure(fg=PANEL_DIM, bg=PANEL_BG)
                frames[n].pack(fill="x")
                labels[n].configure(fg="#ffffff", bg=PANEL_GOLD)
                self.win.after(30, self.fix_scroll)

            lab.bind("<Button-1>", go)
        first = names[0]
        frames[first].pack(fill="x")
        labels[first].configure(fg="#ffffff", bg=PANEL_GOLD)
        return frames

    def build_anim(self, page):
        tabs = self.subtabs(page, ["Orb", "Colours", "Orbit", "Waves", "Finish", "Screen"])
        c = self.card(tabs["Orb"], "Signal orb", "The emblem that floats on your "
                      "screen. Drag it anywhere, scroll over it to resize.")
        self.chips(c, ORB_STYLES, settings.get("orb_style", ORB_STYLE),
                   lambda v: (orb_cmds.put(("style", v)),
                              self.status.set("Orb style: %s." % v))).pack(
                                  anchor="w")
        self.slider(c, "Orb size", 90, 300, int(settings.get(
            "orb_size", ORB_SIZE)), lambda v: orb_cmds.put(
                ("size_to", int(v))), step=10, unit="px").pack(anchor="w")
        self.slider(c, "Orb opacity", 30, 100, int(float(settings.get(
            "orb_opacity", 1.0)) * 100), lambda v: (
                save_setting("orb_opacity", int(v) / 100.0),
                orb_cmds.put(("alpha", int(v) / 100.0))),
            step=5, unit="%").pack(anchor="w")
        self.slider(c, "Logo size inside", 60, 130, int(float(settings.get(
            "logo_scale", 1.0)) * 100), lambda v: save_setting(
                "logo_scale", int(v) / 100.0), step=5, unit="%").pack(
                    anchor="w")
        self.slider(c, "Logo spin", 0, 100, int(float(settings.get(
            "logo_spin", 0.0)) * 100), lambda v: save_setting(
                "logo_spin", int(v) / 100.0), step=5, unit="%").pack(
                    anchor="w")
        self.slider(c, "Bounce and float", 0, 200, int(float(settings.get(
            "orb_bob", 1.0)) * 100), lambda v: save_setting(
                "orb_bob", int(v) / 100.0), step=10, unit="%").pack(
                    anchor="w")
        self.switch(c, "Show the orb on screen", True, lambda v: orb_cmds.put(
            ("visible", bool(v)))).pack(anchor="w", pady=(6, 0))

        c = self.card(tabs["Colours"], "Colours", "Pick a palette, let it drift through "
                      "colours (Spectrum), or choose \"Custom\" and set both "
                      "yourself.")
        self.chips(c, list(THEMES), settings.get("theme", DEFAULT_THEME),
                   lambda v: (save_setting("theme", v),
                              self.status.set("Suit colours: %s." % v),
                              self.rebuild_pointer()),
                   columns=4).pack(anchor="w")
        tk.Label(c, text="Custom palette (used when \"Custom\" is picked)",
                 bg=PANEL_CARD, fg=PANEL_DIM, font=(PANEL_FONT, 9)).pack(
                     anchor="w", pady=(10, 4))
        self.color_swatch(c, "Main colour", "custom_a", "#8b6fd0",
                          self.rebuild_pointer).pack(anchor="w", pady=2)
        self.color_swatch(c, "Second colour", "custom_b", "#c9bfe8",
                          self.rebuild_pointer).pack(anchor="w", pady=2)
        tk.Label(c, text="Colour for each mood", bg=PANEL_CARD, fg=PANEL_DIM,
                 font=(PANEL_FONT, 9)).pack(anchor="w", pady=(10, 4))
        moods = tk.Frame(c, bg=PANEL_CARD)
        moods.pack(anchor="w")
        for i, mode in enumerate(("idle", "listening", "thinking",
                                  "speaking")):
            cur = (settings.get("mode_colors") or {}).get(mode, PANEL_EDGE)
            b = self.button(moods, mode.title(), self.mode_color(mode, cur))
            b.grid(row=0, column=i, padx=(0, 6))
        self.button(moods, "Reset moods", lambda: (
            save_setting("mode_colors", {}),
            self.status.set("Mood colours back to the palette.")),
            kind="blue").grid(row=0, column=4)

        c = self.card(tabs["Orbit"], "Orbit sparks", "Energy circles your emblem. "
                      "Works with every emblem.")
        self.slider(c, "Orbiting sparks", 0, 8, int(settings.get(
            "orbit_count", 3)), lambda v: save_setting(
                "orbit_count", int(v))).pack(anchor="w")
        self.slider(c, "Orbit speed", 40, 300, int(float(settings.get(
            "orbit_speed", 1.0)) * 100), lambda v: save_setting(
                "orbit_speed", int(v) / 100.0), step=10, unit="%").pack(
                    anchor="w")
        self.slider(c, "Spark size", 50, 250, int(float(settings.get(
            "spark_size", 1.0)) * 100), lambda v: save_setting(
                "spark_size", int(v) / 100.0), step=10, unit="%").pack(
                    anchor="w")
        self.slider(c, "Comet tail length", 0, 20, int(settings.get(
            "orbit_trail", 8)), lambda v: save_setting(
                "orbit_trail", int(v))).pack(anchor="w")
        tk.Label(c, text="Spark shape", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11)).pack(anchor="w", pady=(8, 6))
        self.chips(c, ("dot", "diamond", "star"),
                   settings.get("spark_shape", "dot"),
                   lambda v: save_setting("spark_shape", v)).pack(anchor="w")
        self.switch(c, "Show the orbit paths", settings.get(
            "orbit_paths", True), lambda v: save_setting(
                "orbit_paths", v)).pack(anchor="w", pady=(8, 0))

        c = self.card(tabs["Waves"], "Voice waves", "Rings and bars surge with the "
                      "voice while Optimus talks.")
        self.chips(c, ("ring", "bars", "both", "off"),
                   settings.get("wave_style", "both"),
                   lambda v: save_setting("wave_style", v)).pack(anchor="w")
        self.slider(c, "Wave strength", 40, 250, int(float(settings.get(
            "wave_gain", 1.0)) * 100), lambda v: save_setting(
                "wave_gain", int(v) / 100.0), step=10, unit="%").pack(
                    anchor="w", pady=(6, 0))
        self.button(c, "Preview the waves", self.preview_waves,
                    kind="blue").pack(anchor="w", pady=(6, 0))

        c = self.card(tabs["Finish"], "Rings and dust", "The finishing touches "
                      "around the emblem.")
        tk.Label(c, text="Ring style", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11)).pack(anchor="w", pady=(0, 6))
        self.chips(c, ("rings", "segments", "none"),
                   settings.get("ring_style", "rings"),
                   lambda v: save_setting("ring_style", v)).pack(anchor="w")
        self.switch(c, "Floating dust and sparkles", settings.get(
            "particles", True), lambda v: save_setting("particles", v)).pack(
                anchor="w", pady=(6, 6))
        self.chips(c, ("dust", "stars", "embers"),
                   settings.get("particle_style", "dust"),
                   lambda v: save_setting("particle_style", v)).pack(
                       anchor="w")
        self.slider(c, "Dust amount", 20, 300, int(float(settings.get(
            "particle_density", 1.0)) * 100), lambda v: save_setting(
                "particle_density", int(v) / 100.0), step=10, unit="%").pack(
                    anchor="w", pady=(6, 0))

        c = self.card(tabs["Screen"], "Assemble animation", "A short cinematic that plays "
                      "over your screen when you press Assemble.")
        self.chips(c, ["Random"] + SCREEN_FX + ["Off"],
                   settings.get("screen_fx", "Random"),
                   lambda v: save_setting("screen_fx", v), columns=4).pack(
                       anchor="w")
        row = tk.Frame(c, bg=PANEL_CARD)
        row.pack(anchor="w", pady=(8, 0))
        for name in SCREEN_FX:
            self.button(row, name, lambda n=name: (
                orb_cmds.put(("assemble", n)),
                self.status.set("Playing %s." % n))).pack(
                    side="left", padx=(0, 6))
        self.switch(c, "Play one when Optimus starts", settings.get(
            "startup_fx", False), lambda v: save_setting(
                "startup_fx", v)).pack(anchor="w", pady=(10, 0))


    def preview_waves(self):
        orb_state["demo_until"] = time.time() + 5.0
        self.status.set("Previewing the speaking animation...")

    # ---- page: hero cursor ----
    def build_cursor(self, page):
        c = self.card(page, "Hero pointer", "Inside Optimus your mouse arrow "
                      "becomes a hero pointer carrying the emblem you pick "
                      "below, with a glowing trail and a burst whenever you "
                      "click.")
        self.switch(c, "Use the hero pointer in Optimus", settings.get(
            "hero_pointer", True), self.set_hero_pointer).pack(anchor="w")
        tk.Label(c, text="Effect", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11)).pack(anchor="w", pady=(10, 6))
        self.chips(c, CURSOR_STYLES, settings.get("cursor_style",
                                                   "Hero Cursor"),
                   lambda v: (save_setting("cursor_style", v),
                              self.status.set("Cursor effect: %s." % v)),
                   columns=5).pack(anchor="w")
        tk.Label(c, text="Hero Cursor: trail and sparks on your real pointer."
                 " Sky Jet and Comet: a little flyer that chases it.",
                 bg=PANEL_CARD, fg=PANEL_DIM, font=(PANEL_FONT, 9)).pack(
                     anchor="w", pady=(4, 0))
        tk.Label(c, text="Where", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11)).pack(anchor="w", pady=(10, 6))
        self.chips(c, ("Optimus only", "Whole screen"),
                   settings.get("cursor_scope", "Optimus only"),
                   lambda v: save_setting("cursor_scope", v),
                   columns=4).pack(anchor="w")
        tk.Label(c, text="Click effect", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11)).pack(anchor="w", pady=(10, 6))
        self.chips(c, CLICK_STYLES, settings.get("click_style", "Burst"),
                   lambda v: save_setting("click_style", v),
                   columns=4).pack(anchor="w")
        self.slider(c, "Flyer size", 10, 40, int(settings.get(
            "cursor_size", 22)), lambda v: save_setting(
                "cursor_size", int(v))).pack(anchor="w", pady=(8, 0))
        self.slider(c, "Trail length", 0, 100, int(settings.get(
            "trail_length", 60)), lambda v: save_setting(
                "trail_length", int(v)), step=5, unit="%").pack(anchor="w")

        c = self.card(page, "Pointer emblem", "Pick which hero rides on "
                      "your pointer. \"Same as orb\" follows your orb "
                      "emblem.", accent=PANEL_BLUE)
        self.pointer_grid = tk.Frame(c, bg=PANEL_CARD)
        self.pointer_grid.pack(anchor="w")
        self.pointer_tiles = {}
        self.pointer_thumbs = []
        self.fill_pointer_grid()
        tk.Label(c, text="Move the mouse over this panel to try it. Click "
                 "anything to see the burst.", bg=PANEL_CARD, fg=PANEL_DIM,
                 font=(PANEL_FONT, 9)).pack(anchor="w", pady=(8, 0))
        tk.Label(c, text="Your own flyer: save a picture as "
                 "cursor_sprite.png in the Optimus folder, facing right, "
                 "then pick \"Custom Sprite\".", bg=PANEL_CARD,
                 fg=PANEL_DIM, font=(PANEL_FONT, 9)).pack(anchor="w")

    def fill_pointer_grid(self):
        from PIL import Image, ImageTk
        for child in self.pointer_grid.winfo_children():
            child.destroy()
        self.pointer_thumbs.clear()
        self.pointer_tiles.clear()
        options = [("Same as orb", None)] + list_logos()
        current = settings.get("cursor_emblem")
        for index, (label, rel) in enumerate(options):
            tile = tk.Frame(self.pointer_grid, bg=PANEL_CARD2,
                            cursor=hand_cursor(), highlightthickness=2,
                            highlightbackground=PANEL_RED if rel == current
                            else PANEL_EDGE)
            tile.grid(row=index // 6, column=index % 6, padx=(0, 8),
                      pady=(0, 8))
            try:
                path = (os.path.join(BASE_DIR, rel) if rel
                        else current_logo_path())
                logo = prepare_logo(path).convert("RGBA").resize(
                    (46, 46), Image.LANCZOS)
                photo = ImageTk.PhotoImage(logo)
                self.pointer_thumbs.append(photo)
                picture = tk.Label(tile, image=photo, bg=PANEL_CARD2,
                                   cursor=hand_cursor())
            except Exception:
                picture = tk.Label(tile, text="?", bg=PANEL_CARD2,
                                   fg=PANEL_DIM, cursor=hand_cursor())
            picture.pack(padx=8, pady=(8, 2))
            name = tk.Label(tile, text=(label if len(label) <= 11 else label[:10] + "\u2026"), bg=PANEL_CARD2,
                            fg=PANEL_DIM, font=(PANEL_FONT, 8, "bold"),
                            cursor=hand_cursor())
            name.pack(pady=(0, 6))
            for widget in (tile, picture, name):
                widget.bind("<Button-1>",
                            lambda e, r=rel, l=label: self.pick_pointer(r, l))
            self.pointer_tiles[rel] = tile

    def pick_pointer(self, rel, label):
        save_setting("cursor_emblem", rel)
        for key, tile in self.pointer_tiles.items():
            tile.configure(highlightbackground=PANEL_RED if key == rel
                           else PANEL_EDGE)
        self.rebuild_pointer()
        self.status.set("Pointer emblem: %s." % label)

    def set_hero_pointer(self, value):
        save_setting("hero_pointer", bool(value))
        if value:
            self.rebuild_pointer()
        else:
            try:
                self.win.configure(cursor="arrow")
                self.reset_cursors(self.win, "hand2")
            except tk.TclError:
                pass
        self.status.set("Hero pointer %s." % ("on" if value else "off"))

    def reset_cursors(self, widget, hand):
        try:
            if str(widget.cget("cursor")) in CURSOR_LOOK["old"] | {
                    CURSOR_LOOK["hand"]}:
                widget.configure(cursor=hand)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.reset_cursors(child, hand)

    def rebuild_pointer(self):
        """Rebuild the hero pointer after an emblem or colour change."""
        if refresh_cursor_look():
            apply_cursor_look(self.win)

    # ---- page: loadouts ----
    def build_loadout(self, page):
        c = self.card(page, "Hero loadouts", "One click sets the colours, "
                      "voice, personality, orbit and emblem together. You can "
                      "still tweak everything afterwards.")
        grid = tk.Frame(c, bg=PANEL_CARD)
        grid.pack(anchor="w")
        for i, (name, tagline, emblem, values) in enumerate(LOADOUTS):
            tile = tk.Frame(grid, bg=PANEL_CARD2, cursor=hand_cursor(),
                            highlightthickness=2,
                            highlightbackground=PANEL_EDGE)
            tile.grid(row=i // 2, column=i % 2, padx=(0, 12), pady=(0, 12))
            pa, pb = THEMES[values["theme"]]
            bar = tk.Canvas(tile, width=330, height=6, bg=PANEL_CARD2,
                            highlightthickness=0)
            bar.pack()
            bar.create_rectangle(0, 0, 165, 6, fill=pa, outline="")
            bar.create_rectangle(165, 0, 330, 6, fill=pb, outline="")
            title = tk.Label(tile, text=name.upper(), bg=PANEL_CARD2,
                             fg=PANEL_TEXT, font=(PANEL_FONT, 12, "bold"),
                             anchor="w", padx=14, cursor=hand_cursor())
            title.pack(fill="x", pady=(10, 0))
            note = tk.Label(tile, text=tagline, bg=PANEL_CARD2, fg=PANEL_DIM,
                            font=(PANEL_FONT, 10), anchor="w", padx=14,
                            cursor=hand_cursor())
            note.pack(fill="x", pady=(0, 12))
            for widget in (tile, title, note):
                widget.bind("<Button-1>", lambda e, n=i: self.apply_loadout(n))
                widget.bind("<Enter>", lambda e, t=tile: t.configure(
                    highlightbackground=PANEL_BLUE))
                widget.bind("<Leave>", lambda e, t=tile: t.configure(
                    highlightbackground=PANEL_EDGE))

    def apply_loadout(self, index):
        name, tagline, emblem, values = LOADOUTS[index]
        for key, value in values.items():
            save_setting(key, value)
        rel = find_logo(emblem)
        if rel:
            save_setting("logo_file", rel)
            save_setting("cursor_emblem", rel)
            orb_cmds.put(("logo",))
            threading.Thread(target=refresh_tray_icon, daemon=True).start()
            self.load_badge()
            self.set_window_icon()
        self.rebuild_pointer()
        for key in ("anim", "cursor", "voice"):
            self.refresh_page(key)
        self.fill_logos()
        orb_state["demo_until"] = time.time() + 3.0
        self.flash = 1.0
        self.status.set("%s loadout equipped. %s" % (name, tagline))

    def refresh_page(self, key):
        page = self.pages[key]
        for child in page.winfo_children():
            child.destroy()
        self.builders[key](self.scroll_page(page, key))
        if self.current == key:
            self.active_canvas = self.scrollers.get(key)
        apply_cursor_look(page)

    # ---- page: voice ----
    def build_voice(self, page):
        c = self.card(page, "Voice comms", "Pick the voice on the other end of the "
                      "line. Click one to switch and hear it.")
        grid = tk.Frame(c, bg=PANEL_CARD)
        grid.pack(anchor="w")
        self.voice_cards = {}
        packs = self.available_packs()
        current = current_style()
        for i, name in enumerate(packs):
            pack = VOICE_PACKS[name]
            tile = tk.Frame(grid, bg=PANEL_CARD2, cursor=hand_cursor(),
                            highlightthickness=2,
                            highlightbackground=PANEL_RED if name == current
                            else PANEL_EDGE)
            tile.grid(row=i // 3, column=i % 3, padx=(0, 10), pady=(0, 10))
            title = tk.Label(tile, text=pack[4], bg=PANEL_CARD2,
                             fg=PANEL_TEXT, font=(PANEL_FONT, 12, "bold"),
                             width=17, anchor="w", padx=12)
            title.pack(pady=(10, 0))
            note = tk.Label(tile, text=pack[5], bg=PANEL_CARD2, fg=PANEL_DIM,
                            font=(PANEL_FONT, 9), anchor="w", padx=12)
            note.pack(fill="x", pady=(0, 10))
            for widget in (tile, title, note):
                widget.bind("<Button-1>", lambda e, n=name: self.pick_voice(n))
                widget.bind("<Enter>", lambda e, t=tile, n=name:
                            t.configure(highlightbackground=PANEL_BLUE)
                            if n != current_style() else None)
                widget.bind("<Leave>", lambda e, t=tile, n=name:
                            t.configure(highlightbackground=PANEL_RED
                                        if n == current_style()
                                        else PANEL_EDGE))
            self.voice_cards[name] = tile
        self.slider(c, "Speaking speed", 70, 130, int(float(settings.get(
            "voice_speed", 1.0)) * 100), lambda v: save_setting(
                "voice_speed", int(v) / 100.0), step=5, unit="%").pack(
                    anchor="w", pady=(4, 0))
        self.button(c, "Test this voice", lambda: say(
            "This is how I sound now, %s." % USER_NAME), kind="blue").pack(
                anchor="w", pady=(6, 0))

        c = self.card(page, "Attitude", "How Optimus talks to you.",
                      accent=PANEL_BLUE)
        self.chips(c, list(MODES), settings.get("mode", "normal"),
                   lambda v: (save_setting("mode", v),
                              self.status.set("Personality: %s." % v)),
                   columns=5).pack(anchor="w")

    def available_packs(self):
        names = list(VOICE_PACKS)
        if tts is not None:
            try:
                have = set(tts.get_voices())
                names = [n for n in names if VOICE_PACKS[n][0] in have]
            except Exception:
                pass
        return names or ["jarvis"]

    def pick_voice(self, name):
        save_setting("voice_style", name)
        for key, tile in self.voice_cards.items():
            tile.configure(highlightbackground=PANEL_RED if key == name
                           else PANEL_EDGE)
        self.status.set("Voice: %s." % VOICE_PACKS[name][4])
        say("Hi, I'm %s. This is my voice." % VOICE_PACKS[name][4])

    # ---- page: keys and shortcuts ----
    def combo_picker(self, parent, combo, on_change, bg=PANEL_CARD):
        parsed = parse_combo(combo)
        info = {"mods": set(parsed[0]) if parsed else set(),
                "key": next((k for k, v in COMBO_KEYS.items()
                             if parsed and v == parsed[1]), "-")}
        frame = tk.Frame(parent, bg=bg)
        labels = {}

        def paint():
            for name, lab in labels.items():
                on = name in info["mods"]
                lab.configure(bg=PANEL_BLUE if on else PANEL_CARD2,
                              fg=PANEL_INK if on else PANEL_DIM)

        def changed():
            paint()
            on_change(build_combo(info["mods"], info["key"]))

        for name, _ in COMBO_MODS:
            lab = tk.Label(frame, text=name.capitalize(), bg=PANEL_CARD2,
                           fg=PANEL_DIM, cursor=hand_cursor(),
                           font=(PANEL_FONT, 10, "bold"), padx=10, pady=5)
            lab.pack(side="left", padx=(0, 4))

            def flip(event, n=name):
                info["mods"] ^= {n}
                changed()

            lab.bind("<Button-1>", flip)
            labels[name] = lab
        var = tk.StringVar(master=self.win, value=info["key"])

        def pick(value):
            info["key"] = value
            changed()

        self.menu(frame, var, ["-"] + COMBO_KEY_LIST, pick, width=6).pack(
            side="left", padx=(4, 0))
        paint()
        return frame

    def build_keys(self, page):
        c = self.card(page, "Comm key", "Hold this key and speak. Tap it to cut "
                      "Optimus off while it talks.")
        row = tk.Frame(c, bg=PANEL_CARD)
        row.pack(anchor="w")
        current = str(settings.get("ptt_key", PTT_KEY)) or "none"
        var = tk.StringVar(master=self.win, value=current)
        tk.Label(row, text="Talk key", bg=PANEL_CARD, fg=PANEL_TEXT,
                 font=(PANEL_FONT, 11), width=12, anchor="w").pack(
                     side="left")
        self.menu(row, var, ["none"] + PTT_CHOICES, lambda v: (
            save_setting("ptt_key", "" if v == "none" else v),
            self.status.set("Talk key: %s." % v)), width=16).pack(side="left")

        c = self.card(page, "Team hotkeys", "Work in any app. Pick "
                      "Ctrl, Alt or Shift plus a key. Set the key to - to "
                      "turn one off.", accent=PANEL_BLUE)
        saved = get_hotkeys()
        for action, label, default in HOTKEY_ACTIONS:
            row = tk.Frame(c, bg=PANEL_CARD)
            row.pack(anchor="w", pady=3)
            tk.Label(row, text=label, bg=PANEL_CARD, fg=PANEL_TEXT,
                     font=(PANEL_FONT, 11), width=30, anchor="w").pack(
                         side="left")

            def changed(combo, a=action):
                keys = dict(settings.get("hotkeys") or {})
                keys[a] = combo
                save_setting("hotkeys", keys)
                self.status.set("Shortcut saved: %s." % pretty_combo(combo))

            self.combo_picker(row, saved.get(action, default),
                              changed).pack(side="left")

        c = self.card(page, "Custom missions", "A key combination that runs any "
                      "command you like.")
        self.shortcut_list = tk.Frame(c, bg=PANEL_CARD)
        self.shortcut_list.pack(anchor="w", fill="x")
        form = tk.Frame(c, bg=PANEL_CARD)
        form.pack(anchor="w", pady=(8, 0))
        self.new_combo = {"value": ""}
        self.combo_picker(form, "", lambda v: self.new_combo.update(
            value=v)).pack(side="left")
        tk.Label(form, text=" runs ", bg=PANEL_CARD, fg=PANEL_DIM,
                 font=(PANEL_FONT, 10)).pack(side="left")
        self.new_command = self.entry(form, width=26)
        self.new_command.pack(side="left", ipady=5)
        self.button(form, "Add", self.add_shortcut, kind="red",
                    padx=14).pack(side="left", padx=(8, 0))
        self.refresh_shortcuts()

        c = self.card(page, "Battle cries", "Teach Optimus a new phrase. Saying "
                      "\"Optimus work mode\" can run \"open chrome\".",
                      accent=PANEL_BLUE)
        self.phrase_list = tk.Frame(c, bg=PANEL_CARD)
        self.phrase_list.pack(anchor="w", fill="x")
        form = tk.Frame(c, bg=PANEL_CARD)
        form.pack(anchor="w", pady=(8, 0))
        tk.Label(form, text="When I say", bg=PANEL_CARD, fg=PANEL_DIM,
                 font=(PANEL_FONT, 10)).pack(side="left")
        self.new_phrase = self.entry(form, width=18)
        self.new_phrase.pack(side="left", ipady=5, padx=6)
        tk.Label(form, text="do", bg=PANEL_CARD, fg=PANEL_DIM,
                 font=(PANEL_FONT, 10)).pack(side="left")
        self.new_phrase_cmd = self.entry(form, width=24)
        self.new_phrase_cmd.pack(side="left", ipady=5, padx=6)
        self.button(form, "Add", self.add_phrase, kind="red",
                    padx=14).pack(side="left")
        self.refresh_phrases()

    def refresh_shortcuts(self):
        for child in self.shortcut_list.winfo_children():
            child.destroy()
        items = get_shortcuts()
        if not items:
            tk.Label(self.shortcut_list, text="None yet.", bg=PANEL_CARD,
                     fg=PANEL_DIM, font=(PANEL_FONT, 10)).pack(anchor="w")
        for index, item in enumerate(items):
            row = tk.Frame(self.shortcut_list, bg=PANEL_CARD)
            row.pack(anchor="w", pady=2, fill="x")
            tk.Label(row, text="%s   runs   %s" % (
                pretty_combo(item["combo"]), item["command"]),
                bg=PANEL_CARD, fg=PANEL_TEXT, font=(PANEL_FONT, 11)).pack(
                    side="left")
            self.button(row, "Remove", lambda i=index: self.remove_shortcut(i),
                        padx=10).pack(side="left", padx=10)

    def add_shortcut(self):
        combo = self.new_combo["value"]
        command = self.new_command.get().strip()
        if not parse_combo(combo):
            self.status.set("Pick Ctrl, Alt or Shift and a key first.")
            return
        if not command:
            self.status.set("Type the command it should run.")
            return
        items = get_shortcuts() + [{"combo": combo, "command": command}]
        save_setting("shortcuts", items)
        self.new_command.delete(0, "end")
        self.refresh_shortcuts()
        self.status.set("Shortcut added: %s." % pretty_combo(combo))

    def remove_shortcut(self, index):
        items = get_shortcuts()
        if 0 <= index < len(items):
            items.pop(index)
            save_setting("shortcuts", items)
        self.refresh_shortcuts()

    def refresh_phrases(self):
        for child in self.phrase_list.winfo_children():
            child.destroy()
        phrases = get_phrases()
        if not phrases:
            tk.Label(self.phrase_list, text="None yet.", bg=PANEL_CARD,
                     fg=PANEL_DIM, font=(PANEL_FONT, 10)).pack(anchor="w")
        for phrase, command in phrases.items():
            row = tk.Frame(self.phrase_list, bg=PANEL_CARD)
            row.pack(anchor="w", pady=2, fill="x")
            tk.Label(row, text="\"%s\"   does   %s" % (phrase, command),
                     bg=PANEL_CARD, fg=PANEL_TEXT,
                     font=(PANEL_FONT, 11)).pack(side="left")
            self.button(row, "Remove",
                        lambda p=phrase: self.remove_phrase(p),
                        padx=10).pack(side="left", padx=10)

    def add_phrase(self):
        phrase = phrase_key(self.new_phrase.get())
        command = self.new_phrase_cmd.get().strip()
        if not phrase or not command:
            self.status.set("Fill in both boxes.")
            return
        phrases = dict(get_phrases())
        phrases[phrase] = command
        save_setting("phrases", phrases)
        self.new_phrase.delete(0, "end")
        self.new_phrase_cmd.delete(0, "end")
        self.refresh_phrases()
        self.status.set("Phrase added: %s." % phrase)

    def remove_phrase(self, phrase):
        phrases = dict(get_phrases())
        phrases.pop(phrase, None)
        save_setting("phrases", phrases)
        self.refresh_phrases()

    # ---- page: system ----
    def build_appearance(self, page):
        c = self.card(page, "Appearance", "Make the panel yours. The accent "
                      "colour changes the buttons, selections and lines.")
        self.chips(c, list(PANEL_ACCENTS) + ["Custom"], settings.get(
            "panel_accent", "Matte Purple"), self.set_panel_accent,
            columns=4).pack(anchor="w")
        self.switch(c, "Glide between pages", settings.get(
            "page_slide", True), lambda v: save_setting(
                "page_slide", v)).pack(anchor="w", pady=(10, 0))
        self.switch(c, "Header light shimmer", settings.get(
            "header_shimmer", True), lambda v: save_setting(
                "header_shimmer", v)).pack(anchor="w", pady=(6, 0))
        self.switch(c, "Open this panel when Optimus starts", settings.get(
            "open_panel_on_start", False), lambda v: save_setting(
                "open_panel_on_start", v)).pack(anchor="w", pady=(6, 0))

    def set_panel_accent(self, name):
        if name == "Custom":
            from tkinter import colorchooser
            picked = colorchooser.askcolor(color=PANEL_GOLD, parent=self.win,
                                           title="Panel accent")
            if not (picked and picked[1]):
                return
            save_setting("panel_custom", picked[1])
        save_setting("panel_accent", name)
        self.status.set("Applying the new look...")
        self.win.after(200, self.reopen)

    def reopen(self):
        self.close()
        orb_cmds.put(("panel",))

    def set_headphones(self, value):
        save_setting("headphones", bool(value))
        self.status.set("Headphone mode ON: only use it with headphones, or "
                        "Optimus will hear itself and stop mid-sentence."
                        if value else "Headphone mode off.")

    def build_system(self, page):
        self.build_appearance(page)
        c = self.card(page, "Deploy Optimus", "Make Optimus a real app: an icon "
                      "with your emblem on the desktop and in the Start menu. "
                      "Clicking it launches Optimus, or opens this panel if "
                      "it's already running.")
        row = tk.Frame(c, bg=PANEL_CARD)
        row.pack(anchor="w")
        self.button(row, "Add to desktop", lambda: self.make_link(
            "Desktop", "the desktop"), kind="red").pack(side="left")
        self.button(row, "Add to Start menu", lambda: self.make_link(
            "Programs", "the Start menu")).pack(side="left", padx=8)
        self.startup_parent = c
        self.startup_switch = None
        self.put_startup_switch(False)
        threading.Thread(target=self.sync_startup_switch,
                         daemon=True).start()

        c = self.card(page, "Protocols", accent=PANEL_BLUE)
        self.switch(c, "Only answer to my voice (voice lock)", lock_enabled(),
                    lambda v: save_setting("voice_lock", v)).pack(anchor="w")
        self.switch(c, "Mute Optimus", state["muted"], self.set_mute).pack(
            anchor="w", pady=(6, 0))
        self.switch(c, "Headphone mode (talk over Optimus) - headphones only",
                    headphones_on(), self.set_headphones).pack(
                        anchor="w", pady=(6, 0))
        self.switch(c, "Open this panel when Optimus starts",
                    settings.get("open_panel_on_start", False),
                    lambda v: save_setting("open_panel_on_start", v)).pack(
                        anchor="w", pady=(6, 0))

        c = self.card(page, "Base operations")
        row = tk.Frame(c, bg=PANEL_CARD)
        row.pack(anchor="w")
        self.button(row, "Open the Optimus folder", lambda: self.open_path(
            BASE_DIR)).pack(side="left")
        self.button(row, "Quit Optimus", lambda: os._exit(0),
                    kind="red").pack(side="left", padx=8)

    def open_path(self, path):
        try:
            os.startfile(path)
        except Exception as error:
            self.status.set("Couldn't open that: %s" % error)

    def set_mute(self, value):
        state["muted"] = bool(value)
        apply_mute_icon()

    def make_link(self, kind, where):
        self.status.set("Creating the icon...")

        def work():
            try:
                create_shortcut(kind)
                message = "Done. Optimus is now on %s." % where
            except Exception as error:
                message = "Couldn't create the icon: %s" % error
            self.ui_calls.put(lambda: self.status.set(message))

        threading.Thread(target=work, daemon=True).start()

    def set_startup(self, value):
        def work():
            try:
                if value:
                    create_shortcut("Startup")
                    message = "Optimus will start with Windows."
                else:
                    remove_shortcut("Startup")
                    message = "Optimus will no longer start with Windows."
            except Exception as error:
                message = "Couldn't change that: %s" % error
            self.ui_calls.put(lambda: self.status.set(message))

        threading.Thread(target=work, daemon=True).start()

    def put_startup_switch(self, value):
        if self.startup_switch is not None:
            self.startup_switch.destroy()
        self.startup_switch = self.switch(
            self.startup_parent, "Start Optimus when Windows starts", value,
            self.set_startup)
        self.startup_switch.pack(anchor="w", pady=(10, 0))

    def sync_startup_switch(self):
        exists = shortcut_exists("Startup")
        if exists:
            self.ui_calls.put(lambda: self.put_startup_switch(True))


# ======================== cut a sheet of logos into separate logos ========================
SHEET_NAMES = ["S.H.I.E.L.D.", "Hulk", "Captain America", "Spider-Man",
               "Iron Man", "Avengers", "Black Widow", "Captain Marvel",
               "Thor", "Hawkeye", "Doctor Strange"]


def split_logo_sheet(path):
    """Cut a picture that holds many logos on a white background into one
    transparent PNG per logo (saved in the logos folder). Returns the list of
    (label, relative path)."""
    from PIL import Image, ImageDraw, ImageFilter
    sheet = Image.open(path).convert("RGB")
    w, h = sheet.size
    arr = np.asarray(sheet)
    near_white = (arr > 236).all(axis=2)
    # the white that touches the picture's edge is background
    step = 4
    hh, ww = (h // step) * step, (w // step) * step
    blocks = near_white[:hh, :ww].reshape(hh // step, step, ww // step,
                                          step).all(axis=(1, 3))
    reach = np.zeros(blocks.shape, bool)
    todo = collections.deque()
    for sy in range(blocks.shape[0]):
        for sx in (0, blocks.shape[1] - 1):
            if blocks[sy, sx] and not reach[sy, sx]:
                reach[sy, sx] = True
                todo.append((sy, sx))
    for sx in range(blocks.shape[1]):
        for sy in (0, blocks.shape[0] - 1):
            if blocks[sy, sx] and not reach[sy, sx]:
                reach[sy, sx] = True
                todo.append((sy, sx))
    while todo:
        y, x = todo.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if (0 <= ny < blocks.shape[0] and 0 <= nx < blocks.shape[1]
                    and blocks[ny, nx] and not reach[ny, nx]):
                reach[ny, nx] = True
                todo.append((ny, nx))
    outside = np.zeros((h, w), bool)
    outside[:hh, :ww] = np.kron(reach, np.ones((step, step), bool))
    outside &= near_white
    for _ in range(4):          # take in the soft white edge of each logo
        grown = outside.copy()
        grown[1:, :] |= outside[:-1, :]
        grown[:-1, :] |= outside[1:, :]
        grown[:, 1:] |= outside[:, :-1]
        grown[:, :-1] |= outside[:, 1:]
        outside = grown & near_white
    foreground = ~outside
    # find the separate logos on a shrunken map (thin lines stay in)
    small = foreground[:hh, :ww].reshape(hh // step, step, ww // step,
                                         step).any(axis=(1, 3))
    labels = np.zeros(small.shape, np.int32)
    count = 0
    for sy, sx in zip(*np.nonzero(small)):
        if labels[sy, sx]:
            continue
        count += 1
        todo = collections.deque([(sy, sx)])
        labels[sy, sx] = count
        while todo:
            y, x = todo.popleft()
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if (0 <= ny < small.shape[0] and 0 <= nx < small.shape[1]
                            and small[ny, nx] and not labels[ny, nx]):
                        labels[ny, nx] = count
                        todo.append((ny, nx))
    pieces = []
    for number in range(1, count + 1):
        ys, xs = np.nonzero(labels == number)
        if len(ys) < 40:            # specks, not logos
            continue
        pieces.append((int(ys.min()) * step, int(ys.max() + 1) * step,
                       int(xs.min()) * step, int(xs.max() + 1) * step, number))
    # reading order: top to bottom in rows, then left to right
    pieces.sort(key=lambda p: ((p[0] + p[1]) / 2.0, (p[2] + p[3]) / 2.0))
    rows, current = [], []
    for piece in pieces:
        if current and (piece[0] + piece[1]) / 2.0 - (
                current[0][0] + current[0][1]) / 2.0 > 140:
            rows.append(current)
            current = []
        current.append(piece)
    if current:
        rows.append(current)
    ordered = [p for row in rows for p in sorted(row, key=lambda q: q[2])]
    os.makedirs(LOGO_DIR, exist_ok=True)
    result = []
    for index, (y0, y1, x0, x1, number) in enumerate(ordered):
        y1, x1 = min(h, y1), min(w, x1)
        mine = np.kron(labels[y0 // step:y1 // step, x0 // step:x1 // step]
                       == number, np.ones((step, step), bool))
        mine = mine[:y1 - y0, :x1 - x0]
        keep = foreground[y0:y1, x0:x1] & mine
        alpha = Image.fromarray((keep * 255).astype(np.uint8), "L")
        alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
        tile = sheet.crop((x0, y0, x1, y1)).convert("RGBA")
        tile.putalpha(alpha)
        side = max(tile.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(tile, ((side - tile.width) // 2,
                            (side - tile.height) // 2))
        square = square.resize((512, 512), Image.LANCZOS)
        label = (SHEET_NAMES[index] if len(ordered) == len(SHEET_NAMES)
                 else "Hero %d" % (index + 1))
        fname = "hero_%02d_%s.png" % (index + 1, re.sub(
            r"[^a-z0-9]+", "_", label.lower()).strip("_"))
        square.save(os.path.join(LOGO_DIR, fname))
        result.append((label, "logos/" + fname))
    return result


# ======================== hero mouse pointer (inside Optimus) ========================
CURSOR_LOOK = {"arrow": "arrow", "hand": "hand2", "key": None, "ok": True,
               "old": {"hand2"}}


def arrow_cursor():
    return CURSOR_LOOK["arrow"]


def hand_cursor():
    return CURSOR_LOOK["hand"]


def write_cur_file(path, image, hotspot):
    """Save an RGBA picture as a Windows .cur mouse pointer file."""
    import struct
    image = image.convert("RGBA")
    w, h = image.size
    pixels = np.asarray(image)[:, :, [2, 1, 0, 3]][::-1]       # BGRA, bottom up
    xor = np.ascontiguousarray(pixels).tobytes()
    mask = bytes(((w + 31) // 32) * 4 * h)
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0,
                         len(xor) + len(mask), 0, 0, 0, 0)
    data = header + xor + mask
    entry = struct.pack("<BBBBHHII", w, h, 0, 0, hotspot[0], hotspot[1],
                        len(data), 22)
    with open(path, "wb") as handle:
        handle.write(struct.pack("<HHH", 0, 2, 1) + entry + data)


def build_cursor_image(emblem_path, hand=False):
    """An arrow with the chosen hero emblem next to it (48 px)."""
    from PIL import Image, ImageDraw
    pa, pb = theme_colors()
    size, scale = 48, 4
    big = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def px(*values):
        return tuple(v * scale for v in values)

    cx, cy, r = 31, 31, 14
    if hand:
        d.ellipse(px(cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3),
                  fill=pb)
        for k in range(8):
            a = math.radians(k * 45 + 22)
            d.ellipse(px(cx + math.cos(a) * (r + 6) - 1.5,
                         cy + math.sin(a) * (r + 6) - 1.5,
                         cx + math.cos(a) * (r + 6) + 1.5,
                         cy + math.sin(a) * (r + 6) + 1.5), fill="#ffffff")
    d.ellipse(px(cx - r, cy - r, cx + r, cy + r), fill="#0a1126")
    d.ellipse(px(cx - r, cy - r, cx + r, cy + r), outline=pa,
              width=2 * scale)
    try:
        logo = prepare_logo(emblem_path).convert("RGBA")
        inner = int((r - 2) * 2 * scale)
        logo = logo.resize((inner, inner), Image.LANCZOS)
        big.alpha_composite(logo, (int((cx - r + 2) * scale),
                                   int((cy - r + 2) * scale)))
    except Exception:
        pass
    arrow = [(2, 2), (2, 31), (9, 24), (14, 36), (19, 34), (14, 23),
             (24, 23)]
    d.polygon([px(*p) for p in arrow], fill="#0a1126", outline="#0a1126",
              width=5 * scale // 2)
    d.polygon([px(*p) for p in arrow], fill=pa, outline="#ffffff",
              width=scale + 2)
    return big.resize((size, size), Image.LANCZOS)


def _cursor_works(spec):
    """True if this system accepts the pointer file (checked, never assumed)."""
    try:
        probe = tk.Frame(tk._default_root)
        probe.configure(cursor=spec)
        probe.destroy()
        return True
    except Exception:
        return False


def refresh_cursor_look():
    """Make the .cur files for the chosen emblem and switch the pointer."""
    if not CURSOR_LOOK["ok"] or not settings.get("hero_pointer", True):
        return False
    try:
        import hashlib
        rel = settings.get("cursor_emblem")
        path = os.path.join(BASE_DIR, rel) if rel else current_logo_path()
        if not os.path.exists(path):
            path = current_logo_path()
        pa, pb = theme_colors()
        tag = hashlib.md5(("%s|%s|%s|%s" % (path, os.path.getmtime(path),
                                            pa, pb)).encode()).hexdigest()[:8]
        if tag == CURSOR_LOOK["key"]:
            return False
        folder = os.path.join(BASE_DIR, "cursors")
        os.makedirs(folder, exist_ok=True)
        arrow = os.path.join(folder, "arrow_%s.cur" % tag)
        hand = os.path.join(folder, "hand_%s.cur" % tag)
        if not os.path.exists(arrow):
            write_cur_file(arrow, build_cursor_image(path), (2, 2))
        if not os.path.exists(hand):
            write_cur_file(hand, build_cursor_image(path, True), (2, 2))
        def adopt(files):
            for spec_format in ("@%s", "@{%s}"):
                specs = [spec_format % f.replace("\\", "/") for f in files]
                if all(_cursor_works(sp) for sp in specs):
                    return specs
            return None

        found = adopt((arrow, hand))
        if found is None:      # paths with odd characters: try a plain folder
            plain = os.path.join(os.environ.get("PUBLIC", BASE_DIR),
                                 "OptimusCursors")
            try:
                os.makedirs(plain, exist_ok=True)
                copies = []
                for f in (arrow, hand):
                    target = os.path.join(plain, os.path.basename(f))
                    shutil.copy2(f, target)
                    copies.append(target)
                found = adopt(copies)
            except OSError:
                found = None
        if found is None:
            CURSOR_LOOK["ok"] = False
            print("This system doesn't accept the hero pointer file, so the "
                  "normal pointer stays.")
            return False
        arrow_spec, hand_spec = found
        CURSOR_LOOK["old"] |= {CURSOR_LOOK["arrow"], CURSOR_LOOK["hand"]}
        CURSOR_LOOK["arrow"] = arrow_spec
        CURSOR_LOOK["hand"] = hand_spec
        CURSOR_LOOK["key"] = tag
        return True
    except Exception as error:
        print("Hero pointer unavailable:", error)
        return False


def apply_cursor_look(widget):
    """Give a window and everything in it the hero pointer."""
    if not settings.get("hero_pointer", True) or not CURSOR_LOOK["ok"]:
        return

    def walk(w):
        try:
            current = str(w.cget("cursor"))
        except tk.TclError:
            current = None
        if current is not None and (current in CURSOR_LOOK["old"]):
            w.configure(cursor=CURSOR_LOOK["hand"])
        for child in w.winfo_children():
            walk(child)

    try:
        widget.configure(cursor=CURSOR_LOOK["arrow"])
        walk(widget)
    except tk.TclError as error:
        CURSOR_LOOK["ok"] = False
        CURSOR_LOOK["arrow"], CURSOR_LOOK["hand"] = "arrow", "hand2"
        print("Windows refused the hero pointer, using the normal one:", error)
        try:
            widget.configure(cursor="arrow")
            walk(widget)
        except tk.TclError:
            pass


# ======================== flying cursor and click effects ========================
CURSOR_STYLES = ("Hero Cursor", "Sky Jet", "Comet", "Custom sprite", "Off")
CLICK_STYLES = ("Burst", "Sparks", "Ripple", "Off")
SPRITE_FILE = "cursor_sprite.png"    # your own picture, pointing to the right
JET_BODY = [(1.0, 0), (0.1, 0.16), (-0.6, 0.62), (-0.45, 0.12), (-0.62, 0),
            (-0.45, -0.12), (-0.6, -0.62), (0.1, -0.16)]
JET_WING = [(0.05, 0.2), (-0.45, 0.52), (-0.38, 0.22)]
JET_CANOPY = [(0.6, 0), (0.18, 0.1), (0.02, 0), (0.18, -0.1)]


def make_click_through(win, key=None):
    """Let clicks pass through this window, and make its key colour see-through."""
    try:
        user32 = ctypes.windll.user32
        win.update_idletasks()
        hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
        style = user32.GetWindowLongW(hwnd, -20)
        user32.SetWindowLongW(
            hwnd, -20, style | 0x80000 | 0x20 | 0x80 | 0x08000000)
        if key:
            red, green, blue = (int(key[i:i + 2], 16) for i in (1, 3, 5))
            user32.SetLayeredWindowAttributes(
                hwnd, red | (green << 8) | (blue << 16), 255, 0x1)
    except Exception:
        pass


def _heading_step(current, wanted, amount):
    diff = (wanted - current + math.pi) % (2 * math.pi) - math.pi
    return current + diff * min(1.0, amount)


class CursorFX:
    """A tiny hero that flies after your mouse, plus click effects."""
    HALF = 170

    def __init__(self, root, key):
        self.root = root
        self.key = key
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        for attr, value in (("-topmost", True), ("-transparentcolor", key)):
            try:
                self.win.attributes(attr, value)
            except Exception:
                pass
        self.win.configure(bg=key)
        side = self.HALF * 2
        self.canvas = tk.Canvas(self.win, width=side, height=side, bg=key,
                                highlightthickness=0)
        self.canvas.pack()
        self.win.geometry("%dx%d+0+0" % (side, side))
        make_click_through(self.win, key)
        px, py = root.winfo_pointerxy()
        self.x, self.y = float(px) + 40, float(py) + 40
        self.vx = self.vy = 0.0
        self.heading = 0.0
        self.roll = 0.0
        self.roll_v = 0.0
        self.trail = collections.deque(maxlen=60)
        self.sparks = []
        self.ripples = []
        self.last_cursor = (px, py)
        self.last_move = time.time()
        self.down = (False, False)
        self.orbit = 0.0
        self.shown = True
        self.sprites = {}
        self.sprite_base = None
        self.sprite_checked = False
        self.last_top = 0.0
        self.areas = None       # returns the Optimus windows' rectangles

    def inside_optimus(self, px, py):
        try:
            rects = self.areas() if self.areas else []
        except Exception:
            rects = []
        return any(l <= px <= l + w and t <= py <= t + h
                   for l, t, w, h in rects)

    # ---- input ----
    def clicks(self):
        try:
            left = bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
            right = bool(ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000)
        except Exception:
            return False, False, (False, False)
        return left and not self.down[0], right and not self.down[1], \
            (left, right)

    def burst(self, now, px, py, colors):
        style = settings.get("click_style", "Burst")
        if style == "Off":
            return
        pa, pb = colors
        self.ripples.append((now, px, py, style))
        count = {"Burst": 26, "Sparks": 34, "Ripple": 0}.get(style, 20)
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            speed = random.uniform(90, 330 if style == "Sparks" else 240)
            self.sparks.append({
                "x": px, "y": py, "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed, "t0": now,
                "life": random.uniform(0.35, 0.8),
                "col": random.choice((pa, pb, "#ffffff")),
                "r": random.uniform(1.6, 3.6),
                "star": random.random() < 0.4})

    # ---- one frame ----
    def update(self, now, dt):
        style = settings.get("cursor_style", "Hero Cursor")
        if style == "Off":
            if self.shown:
                self.win.withdraw()
                self.shown = False
            return
        px, py = self.root.winfo_pointerxy()
        if (settings.get("cursor_scope", "Optimus only") != "Whole screen"
                and not self.inside_optimus(px, py)):
            if self.shown:      # outside Optimus: stay completely hidden
                self.win.withdraw()
                self.shown = False
                self.down = (False, False)
            self.x, self.y = float(px) + 26, float(py) + 30
            self.vx = self.vy = 0.0
            self.trail.clear()
            return
        if not self.shown:
            self.win.deiconify()
            make_click_through(self.win, self.key)
            self.shown = True
        colors = theme_colors()
        pa, pb = colors
        lclick, rclick, self.down = self.clicks()
        if lclick or rclick:
            self.burst(now, px, py, colors)
            self.roll_v = 16.0 if style != 'Hero Cursor' else 0.0
            self.vx += random.uniform(-260, 260)
            self.vy += random.uniform(-260, 260)
        if math.hypot(px - self.last_cursor[0], py - self.last_cursor[1]) > 2:
            self.last_move = now
        self.last_cursor = (px, py)

        # where the hero wants to be: beside the pointer, or looping round it
        idle = now - self.last_move
        if idle > 2.2:
            self.orbit += dt * 1.7
            r = 58 + 14 * math.sin(now * 0.9)
            tx = px + math.cos(self.orbit) * r
            ty = py + math.sin(self.orbit * 1.0) * r * 0.72
        else:
            self.orbit = math.atan2(self.y - py, self.x - px)
            tx, ty = px + 26, py + 30
        if style == "Hero Cursor":
            # the pointer itself is the hero: just glow, trail and orbit it
            self.vx, self.vy = (px - self.x) / max(dt, 0.001), (
                py - self.y) / max(dt, 0.001)
            self.x, self.y = float(px), float(py)
            speed = min(2600.0, math.hypot(self.vx, self.vy))
            self.vx = self.vy = 0.0
            self.roll_v = 0.0
        else:
            k, damp = 70.0, 11.0
            self.vx += ((tx - self.x) * k - self.vx * damp) * dt
            self.vy += ((ty - self.y) * k - self.vy * damp) * dt
            speed = math.hypot(self.vx, self.vy)
        if style != "Hero Cursor":
            if speed > 2600:
                self.vx, self.vy = (self.vx * 2600 / speed,
                                    self.vy * 2600 / speed)
                speed = 2600
            self.x += self.vx * dt
            self.y += self.vy * dt
        if speed > 45 and style != "Hero Cursor":
            self.heading = _heading_step(self.heading,
                                         math.atan2(self.vy, self.vx),
                                         14 * dt)
        self.roll += self.roll_v * dt
        self.roll_v *= max(0.0, 1 - 3.5 * dt)
        if abs(self.roll_v) < 0.3:
            self.roll = (self.roll + math.pi) % (2 * math.pi) - math.pi
            self.roll *= max(0.0, 1 - 8 * dt)

        # trail
        self.trail.append((self.x, self.y, now))
        span = 0.12 + 0.7 * float(settings.get("trail_length", 60)) / 100.0
        while self.trail and now - self.trail[0][2] > span:
            self.trail.popleft()

        # window follows the hero (and keeps the pointer in view)
        wx, wy = self.x, self.y
        if math.hypot(self.x - px, self.y - py) < self.HALF - 60:
            wx, wy = (self.x + px) / 2.0, (self.y + py) / 2.0
        left = int(wx - self.HALF)
        top = int(wy - self.HALF)
        self.win.geometry("+%d+%d" % (left, top))
        if now - self.last_top > 3:
            self.last_top = now
            try:
                self.win.attributes("-topmost", True)
            except Exception:
                pass
        self.draw(now, dt, left, top, style, speed, colors)

    # ---- drawing ----
    def draw(self, now, dt, left, top, style, speed, colors):
        c = self.canvas
        key = self.key
        pa, pb = colors
        c.delete("all")

        def local(x, y):
            return x - left, y - top

        # trail
        pts = list(self.trail)
        thick = 2.0 + float(settings.get("cursor_size", 22)) / 7.0
        for i in range(1, len(pts)):
            frac = i / float(len(pts))
            (x0, y0, _), (x1, y1, _) = pts[i - 1], pts[i]
            ax, ay = local(x0, y0)
            bx, by = local(x1, y1)
            col = mix_color(mix_color(pb, pa, frac), key, 1 - frac * 0.9)
            c.create_line(ax, ay, bx, by, fill=col, width=max(1, thick * frac),
                          capstyle="round")

        # click ripples
        self.ripples = [r for r in self.ripples if now - r[0] < 0.7]
        for t0, rx, ry, kind in self.ripples:
            age = (now - t0) / 0.7
            x, y = local(rx, ry)
            for n, col in enumerate((pa, pb)):
                rr = 8 + age * (70 if kind == "Ripple" else 52) * (1 - 0.25 * n)
                c.create_oval(x - rr, y - rr, x + rr, y + rr,
                              outline=mix_color(col, key, age), width=3 - n)

        # sparks
        alive = []
        for s in self.sparks:
            age = now - s["t0"]
            if age >= s["life"]:
                continue
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vx"] *= 1 - 2.2 * dt
            s["vy"] *= 1 - 2.2 * dt
            x, y = local(s["x"], s["y"])
            fade = age / s["life"]
            col = mix_color(s["col"], key, fade)
            r = s["r"] * (1 - 0.5 * fade)
            if s["star"]:
                c.create_polygon(x, y - 2 * r, x + r * 0.6, y - r * 0.6,
                                 x + 2 * r, y, x + r * 0.6, y + r * 0.6, x,
                                 y + 2 * r, x - r * 0.6, y + r * 0.6,
                                 x - 2 * r, y, x - r * 0.6, y - r * 0.6,
                                 fill=col, outline="")
            else:
                c.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="")
            alive.append(s)
        self.sparks = alive[-120:]

        # the hero
        x, y = local(self.x, self.y)
        s = float(settings.get("cursor_size", 22))
        if style == "Hero Cursor":
            spin = now * 3.2
            for n in range(3):
                a = spin + n * 2.0944
                orbit = 22 + 3 * math.sin(now * 2 + n)
                for tail in range(5):
                    b = a - tail * 0.16
                    ox, oy = x + math.cos(b) * orbit, y + math.sin(b) * orbit
                    r = max(0.8, 3.2 - tail * 0.55)
                    col = mix_color(pa if n % 2 == 0 else pb, key,
                                    tail * 0.2)
                    c.create_oval(ox - r, oy - r, ox + r, oy + r, fill=col,
                                  outline="")
        elif style == "Comet":
            for rr, col in ((s * 0.95, mix_color(pb, key, 0.7)),
                            (s * 0.62, mix_color(pa, key, 0.35))):
                c.create_oval(x - rr, y - rr, x + rr, y + rr, fill=col,
                              outline="")
            r = s * 0.34
            c.create_oval(x - r, y - r, x + r, y + r, fill="#ffffff",
                          outline=pa, width=2)
        elif style == "Custom sprite" and self.draw_sprite(c, x, y, s):
            pass
        else:
            self.draw_jet(c, x, y, s, speed, colors)

    def draw_jet(self, c, x, y, s, speed, colors):
        pa, pb = colors
        ca, sa = math.cos(self.heading), math.sin(self.heading)
        flat = math.cos(self.roll)

        def shape(points):
            out = []
            for px, py in points:
                py *= flat
                out.extend((x + (px * ca - py * sa) * s,
                            y + (px * sa + py * ca) * s))
            return out

        flame = s * (0.5 + min(speed, 1500) / 700.0) * (
            0.85 + 0.3 * random.random())
        for side in (-1, 1):
            c.create_polygon(shape([(-0.6, side * 0.2), (-0.6 - flame / s,
                                                         side * 0.1),
                                    (-0.6, side * 0.02)]),
                             fill=pb, outline="")
            c.create_polygon(shape([(-0.6, side * 0.15),
                                    (-0.6 - flame / s * 0.55, side * 0.1),
                                    (-0.6, side * 0.05)]),
                             fill="#ffffff", outline="")
        c.create_polygon(shape(JET_BODY), fill=pa, outline="#ffffff", width=1)
        for side in (-1, 1):
            c.create_polygon(shape([(px, py * side) for px, py in JET_WING]),
                             fill=pb, outline="")
        c.create_polygon(shape(JET_CANOPY), fill="#d8f0ff", outline=pb)

    def draw_sprite(self, c, x, y, s):
        from PIL import Image, ImageTk
        if not self.sprite_checked:
            self.sprite_checked = True
            path = os.path.join(BASE_DIR, SPRITE_FILE)
            try:
                if os.path.exists(path):
                    self.sprite_base = Image.open(path).convert("RGBA")
            except Exception as error:
                print("Cursor sprite unavailable:", error)
        if self.sprite_base is None:
            return False
        degrees = int(round(-math.degrees(self.heading) / 6.0)) * 6
        side = int(s * 3.2)
        cache_key = (degrees, side)
        photo = self.sprites.get(cache_key)
        if photo is None:
            if len(self.sprites) > 150:
                self.sprites.clear()
            img = self.sprite_base.copy()
            img.thumbnail((side, side), Image.LANCZOS)
            img = img.rotate(degrees, resample=Image.BICUBIC, expand=True)
            back = Image.new("RGB", img.size, (1, 2, 3))
            back.paste(img, (0, 0), img)
            photo = ImageTk.PhotoImage(back)
            self.sprites[cache_key] = photo
        c.create_image(x, y, image=photo)
        return True


# ======================== full-screen cinematic effects ========================
SCREEN_FX = ["Vibranium Pulse", "Hex Grid", "Cinema Title", "Orbit Lock",
             "Converge"]
SCREEN_FX_DURATION = {"Vibranium Pulse": 4.6, "Hex Grid": 4.6,
                      "Cinema Title": 4.8, "Orbit Lock": 4.8,
                      "Converge": 4.8}
SCREEN_FX_SCENE = {"Vibranium Pulse": "scene_pulse", "Hex Grid": "scene_hex",
                   "Cinema Title": "scene_cinema", "Orbit Lock": "scene_lock",
                   "Converge": "scene_converge"}


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def _spaced(text):
    return "   ".join(" ".join(w) for w in text.split(" "))


class ScreenFX:
    """Quiet, cinematic effects drawn over the screen for a few seconds in
    your orb colours. Click-through, and a click anywhere ends them."""
    BACK = "#000000"

    def __init__(self, root):
        self.root = root
        self.win = None
        self.canvas = None
        self.name = None
        self.start = 0.0
        self.data = {}
        self.photos = []

    def busy(self):
        return self.win is not None

    def play(self, name=None):
        if self.win is not None:
            return
        pick = name or settings.get("screen_fx", "Random")
        if pick == "Off":
            return
        if pick not in SCREEN_FX:
            pick = random.choice(SCREEN_FX)
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        self.w, self.h = w, h
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.geometry("%dx%d+0+0" % (w, h))
        self.win.configure(bg=self.BACK)
        try:
            self.win.attributes("-topmost", True)
            self.win.attributes("-alpha", 0.0)
        except Exception:
            pass
        self.canvas = tk.Canvas(self.win, width=w, height=h, bg=self.BACK,
                                highlightthickness=0)
        self.canvas.pack()
        self.win.bind("<Button-1>", lambda e: self.stop())
        make_click_through(self.win)
        self.name = pick
        self.start = time.time()
        self.data = {}
        self.photos = []
        self.pa, self.pb = theme_colors()
        self.logo = self.emblem(150)
        self.tick()

    def stop(self):
        win, self.win = self.win, None
        self.canvas = None
        self.photos = []
        self.logo = None
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass

    def tick(self):
        if self.win is None:
            return
        try:
            t = time.time() - self.start
            total = SCREEN_FX_DURATION[self.name]
            if t >= total:
                self.stop()
                return
            alpha = min(1.0, t / 0.5, (total - t) / 0.8) * 0.9
            self.win.attributes("-alpha", max(0.0, alpha))
            self.canvas.delete("all")
            getattr(self, SCREEN_FX_SCENE[self.name])(t, self.canvas,
                                                       self.w, self.h)
            self.win.after(30, self.tick)
        except Exception as error:
            print("Screen effect problem:", error)
            self.stop()

    # ---- helpers ----
    def emblem(self, size):
        try:
            from PIL import Image, ImageTk
            img = prepare_logo(current_logo_path()).convert("RGBA")
            photo = ImageTk.PhotoImage(img.resize((size, size),
                                                  Image.LANCZOS))
            self.photos.append(photo)
            return photo
        except Exception:
            return None

    def fade(self, color, k):
        return mix_color(self.BACK, color, max(0.0, min(1.0, k)))

    def text(self, c, text, x, y, k, size=22, color="#f2eef8", style="normal"):
        c.create_text(x, y, text=text, fill=self.fade(color, k),
                      font=(PANEL_FONT, size, style))

    def hair(self, c, x0, x1, y, k, color=None):
        c.create_line(x0, y, x1, y, fill=self.fade(color or self.pa, k),
                      width=1)

    # ---- scenes ----
    def scene_pulse(self, t, c, w, h):
        cx, cy = w / 2.0, h / 2.0
        reach = min(w, h) * 0.55
        for i in range(5):
            age = (t - 0.25 - i * 0.42) / 2.4
            if 0 < age < 1:
                r = _ease(age) * reach
                c.create_oval(cx - r, cy - r, cx + r, cy + r,
                              outline=self.fade(self.pa if i % 2 == 0
                                                else self.pb, 1 - age),
                              width=2 if i == 0 else 1)
        if self.logo is not None and t > 0.3:
            c.create_image(cx, cy, image=self.logo)
        k = _ease((t - 1.0) / 0.8)
        self.text(c, _spaced("OPTIMUS ONLINE"), cx, cy + 150, k, 20)
        half = 160 * _ease((t - 0.9) / 1.0)
        self.hair(c, cx - half, cx + half, cy + 182, 1)

    def scene_hex(self, t, c, w, h):
        cx, cy = w / 2.0, h / 2.0
        r = 38
        dx, dy = r * 1.5, r * math.sqrt(3) / 2.0
        front = t * 0.30 * max(w, h)
        band = 260.0
        cols = int(w / dx) + 3
        rows = int(h / (2 * dy)) + 3
        for i in range(-1, cols):
            for j in range(-1, rows):
                x = i * dx
                y = j * 2 * dy + (dy if i % 2 else 0)
                d = math.hypot(x - cx, y - cy)
                k = 1 - abs(d - front) / band
                if k <= 0.04:
                    continue
                k *= 0.9 * max(0.0, 1 - max(0, t - 3.4) / 1.2)
                pts = []
                for a in range(6):
                    ang = math.radians(60 * a)
                    pts += [x + (r - 3) * math.cos(ang),
                            y + (r - 3) * math.sin(ang)]
                c.create_polygon(pts, outline=self.fade(
                    self.pa if (i + j) % 3 else self.pb, k), fill="",
                    width=1)
        k = _ease((t - 1.3) / 0.7) * min(1.0, (4.6 - t) / 0.6)
        self.text(c, _spaced("SYSTEMS ONLINE"), cx, cy, k, 24)
        half = 120 * _ease((t - 1.2) / 0.9)
        self.hair(c, cx - half, cx + half, cy + 30, k)

    def scene_cinema(self, t, c, w, h):
        cx, cy = w / 2.0, h / 2.0
        bar = h * 0.15 * _ease(t / 0.9) * (
            1 - _ease((t - 4.0) / 0.7))
        c.create_rectangle(0, 0, w, bar, fill="#000000", outline="")
        c.create_rectangle(0, h - bar, w, h, fill="#000000", outline="")
        c.create_line(0, bar, w, bar, fill=self.fade(self.pa, 0.7))
        c.create_line(0, h - bar, w, h - bar, fill=self.fade(self.pa, 0.7))
        k = _ease((t - 1.0) / 1.0)
        self.text(c, _spaced("ASSEMBLE"), cx, cy, k, 54, "#f2eef8")
        sweep = (t - 1.0) / 1.4
        if 0 < sweep < 1:
            x = cx - 380 + sweep * 760
            c.create_line(x, cy - 50, x, cy + 50, fill=self.fade(
                "#ffffff", 0.8), width=2)
        line = QUOTES[int(self.data.setdefault("q", random.randrange(
            len(QUOTES))))]
        self.text(c, line, cx, cy + 66, _ease((t - 2.0) / 0.8), 14,
                  self.pb, "italic")

    def scene_lock(self, t, c, w, h):
        cx, cy = w / 2.0, h / 2.0
        grow = _ease(t / 1.0)
        for i, (rad, speed, count) in enumerate(((95, 70, 3), (135, -45, 4),
                                                  (178, 28, 6))):
            r = rad * grow
            col = self.fade(self.pa if i != 1 else self.pb, 0.9)
            span = 360.0 / count
            for s in range(count):
                c.create_arc(cx - r, cy - r, cx + r, cy + r,
                             start=(t * speed + s * span) % 360,
                             extent=span * 0.62, style="arc", outline=col,
                             width=2 if i != 1 else 1)
        r = 205 * grow
        for deg in range(0, 360, 6):
            a = math.radians(deg + t * 6)
            ln = 12 if deg % 30 == 0 else 5
            c.create_line(cx + math.cos(a) * r, cy + math.sin(a) * r,
                          cx + math.cos(a) * (r + ln),
                          cy + math.sin(a) * (r + ln),
                          fill=self.fade(self.pa, 0.55))
        if self.logo is not None:
            c.create_image(cx, cy, image=self.logo)
        k = _ease((t - 1.4) / 0.7)
        self.text(c, _spaced("IDENTITY CONFIRMED"), cx, cy + 250, k, 18)
        self.text(c, "Optimus is ready.", cx, cy + 284, k, 12, self.pb)

    def scene_converge(self, t, c, w, h):
        cx, cy = w / 2.0, h / 2.0
        d = self.data
        if "dots" not in d:
            d["dots"] = []
            for i in range(180):
                ang = random.uniform(0, 6.2832)
                far = max(w, h) * random.uniform(0.7, 1.0)
                d["dots"].append((cx + math.cos(ang) * far,
                                  cy + math.sin(ang) * far,
                                  ang, random.uniform(0.0, 0.7),
                                  random.choice((self.pa, self.pb))))
        ring = 150
        for sx, sy, ang, delay, col in d["dots"]:
            k = _ease((t - delay) / 2.0)
            tx = cx + math.cos(ang) * ring
            ty = cy + math.sin(ang) * ring
            x, y = sx + (tx - sx) * k, sy + (ty - sy) * k
            if t > 3.0:
                spread = (t - 3.0) * 38
                x += math.cos(ang) * spread
                y += math.sin(ang) * spread
            size = 2 if k < 1 else 1.5
            c.create_oval(x - size, y - size, x + size, y + size,
                          fill=self.fade(col, 0.5 + 0.5 * k), outline="")
        if t > 2.0:
            kk = _ease((t - 2.0) / 1.0) * max(0.0, 1 - (t - 3.8) / 0.8)
            c.create_oval(cx - ring, cy - ring, cx + ring, cy + ring,
                          outline=self.fade(self.pa, kk * 0.8), width=1)
        k = _ease((t - 2.2) / 0.8) * min(1.0, (4.8 - t) / 0.6)
        self.text(c, _spaced("ALL SYSTEMS NOMINAL"), cx, cy, k, 20)


# ======================== your Marvel logo sheet, built in ========================
HERO_LOGO_DATA = {}   # Marvel artwork is not included in the public version


def install_hero_logos():
    """Put the Marvel logos from your sheet into the logos folder (once)."""
    try:
        import base64 as _b64
        os.makedirs(LOGO_DIR, exist_ok=True)
        for name, data in HERO_LOGO_DATA.items():
            path = os.path.join(LOGO_DIR, name)
            if not os.path.exists(path):
                raw = _b64.b64decode("".join(data))
                with open(path, "wb") as f:
                    f.write(raw)
        if HERO_LOGO_DATA and not settings.get("logo_file") and not settings.get("hero_set"):
            settings["hero_set"] = True
            save_setting("logo_file", "logos/hero_06_avengers.png")
    except Exception as error:
        print("Couldn't install the hero logos:", error)


# ======================== keys, shortcuts and phrases ========================
# Every key you can pick as the push-to-talk key (or in a shortcut).
KEY_CODES = {"rightctrl": 0xA3, "leftctrl": 0xA2, "rightalt": 0xA5,
             "leftalt": 0xA4, "rightshift": 0xA1, "capslock": 0x14,
             "scrolllock": 0x91, "numlock": 0x90, "pause": 0x13,
             "insert": 0x2D, "home": 0x24, "end": 0x23, "pageup": 0x21,
             "pagedown": 0x22, "middlemouse": 0x04, "mousebutton4": 0x05,
             "mousebutton5": 0x06}
for _n in range(1, 13):
    KEY_CODES["f%d" % _n] = 0x6F + _n
PTT_CHOICES = ["rightctrl", "leftctrl", "rightalt", "leftalt", "rightshift",
               "capslock", "scrolllock", "pause", "insert", "home", "end",
               "pageup", "pagedown", "middlemouse", "mousebutton4",
               "mousebutton5"] + ["f%d" % n for n in range(1, 13)]

# keys that can go into a shortcut like Ctrl+Alt+O
COMBO_KEYS = {"space": 0x20, "insert": 0x2D, "delete": 0x2E, "home": 0x24,
              "end": 0x23, "pageup": 0x21, "pagedown": 0x22, "up": 0x26,
              "down": 0x28, "left": 0x25, "right": 0x27}
for _c in "abcdefghijklmnopqrstuvwxyz0123456789":
    COMBO_KEYS[_c] = ord(_c.upper())
for _n in range(1, 13):
    COMBO_KEYS["f%d" % _n] = 0x6F + _n
COMBO_MODS = (("ctrl", 0x11), ("alt", 0x12), ("shift", 0x10))
COMBO_KEY_LIST = (list("abcdefghijklmnopqrstuvwxyz0123456789")
                  + ["f%d" % n for n in range(1, 13)]
                  + ["space", "insert", "delete", "home", "end", "pageup",
                     "pagedown", "up", "down", "left", "right"])

HOTKEY_ACTIONS = [   # (id, label, default shortcut)
    ("panel", "Open the control panel", "ctrl+alt+o"),
    ("wake", "Wake Optimus", "ctrl+alt+w"),
    ("stop", "Stop speaking", "ctrl+alt+s"),
    ("mute", "Mute / unmute", "ctrl+alt+m"),
    ("shot", "Take a screenshot", "ctrl+alt+p"),
    ("flier", "Show / hide the flying cursor", "ctrl+alt+f"),
    ("lock", "Voice lock on / off", "ctrl+alt+l"),
    ("assemble", "Avengers, assemble! (screen animation)", "ctrl+alt+a"),
]


def ptt_vk():
    """The push-to-talk key code right now (0 = turned off)."""
    return KEY_CODES.get(str(settings.get("ptt_key", PTT_KEY)).lower(), 0)


def headphones_on():
    return bool(settings.get("headphones", HEADPHONES_MODE))


def parse_combo(text):
    """'ctrl+alt+o' -> (frozenset({'ctrl','alt'}), 0x4F). None if not valid."""
    parts = [p.strip().lower() for p in str(text or "").split("+") if p.strip()]
    if not parts or parts[-1] not in COMBO_KEYS:
        return None
    mods = frozenset(p for p in parts[:-1] if p in ("ctrl", "alt", "shift"))
    if not mods:
        return None     # always needs Ctrl, Alt or Shift so typing is safe
    return mods, COMBO_KEYS[parts[-1]]


def build_combo(mods, key):
    names = [m for m, _ in COMBO_MODS if m in mods]
    return "+".join(names + [key]) if key and names else ""


def pretty_combo(text):
    return " + ".join(p.capitalize() if len(p) > 1 else p.upper()
                      for p in str(text).split("+")) if text else "Off"


def get_hotkeys():
    """{action id: shortcut text} with your changes on top of the defaults."""
    keys = {name: combo for name, label, combo in HOTKEY_ACTIONS}
    keys.update(settings.get("hotkeys") or {})
    return keys


def get_shortcuts():
    items = settings.get("shortcuts") or []
    return [s for s in items if isinstance(s, dict)
            and s.get("combo") and s.get("command")]


def get_phrases():
    items = settings.get("phrases") or {}
    return items if isinstance(items, dict) else {}


def phrase_key(text):
    return " ".join(re.sub(r"[^\w\s]", " ", str(text).lower()).split())


def expand_phrase(command):
    """If you set up 'work mode' -> 'open chrome', turn one into the other."""
    target = get_phrases().get(phrase_key(command))
    return phrase_key(target) if target else command


def combo_down(mods, vk):
    if not key_down(vk):
        return False
    for name, code in COMBO_MODS:
        if (name in mods) != key_down(code):
            return False
    return True


def toggle_flier():
    current = settings.get("cursor_style", "Hero Cursor")
    if current == "Off":
        save_setting("cursor_style", settings.get("cursor_style_last")
                     or "Hero Cursor")
    else:
        save_setting("cursor_style_last", current)
        save_setting("cursor_style", "Off")


def apply_mute_icon():
    icon = tray_ref.get("icon")
    if icon is not None and tray_ref.get("on") is not None:
        try:
            icon.icon = tray_ref["off"] if state["muted"] else tray_ref["on"]
        except Exception:
            pass


def run_hotkey_action(name):
    if name == "panel":
        orb_cmds.put(("panel",))
    elif name == "wake":
        wake_queue.put("wake")
    elif name == "stop":
        stop_speaking()
    elif name == "mute":
        toggle_mute_state()
        apply_mute_icon()
    elif name == "shot":
        typed_queue.put(("take a screenshot", True))
    elif name == "flier":
        toggle_flier()
    elif name == "lock":
        toggle_lock_state()
    elif name == "assemble":
        choice = settings.get("screen_fx", "Random")
        orb_cmds.put(("assemble", None if choice == "Random" else choice))


def hotkey_loop():
    """Watches for your shortcuts, in any app."""
    held = set()
    while True:
        try:
            bindings = []
            for name, combo in get_hotkeys().items():
                parsed = parse_combo(combo)
                if parsed:
                    bindings.append(("a:" + name, parsed))
            for index, item in enumerate(get_shortcuts()):
                parsed = parse_combo(item["combo"])
                if parsed:
                    bindings.append(("s:%d" % index, parsed))
            for ident, (mods, vk) in bindings:
                down = combo_down(mods, vk)
                if down and ident not in held:
                    held.add(ident)
                    kind, _, ref = ident.partition(":")
                    if kind == "a":
                        run_hotkey_action(ref)
                    else:
                        item = get_shortcuts()[int(ref)]
                        typed_queue.put((item["command"], True))
                elif not down:
                    held.discard(ident)
        except Exception as error:
            print("Shortcut watcher problem:", error)
            time.sleep(2)
        time.sleep(0.05)


# ======================== desktop app (shortcuts) ========================
APP_NAME = "Optimus"


def make_icon_file():
    """optimus.ico, drawn from the logo you picked."""
    from PIL import Image
    path = os.path.join(BASE_DIR, "optimus.ico")
    logo = prepare_logo(current_logo_path()).convert("RGBA")
    logo = logo.resize((256, 256), Image.LANCZOS)
    logo.save(path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64),
                                         (48, 48), (32, 32), (16, 16)])
    return path


def launcher_exe():
    """pythonw.exe runs Optimus without a black window."""
    folder = os.path.dirname(sys.executable)
    pythonw = os.path.join(folder, "pythonw.exe")
    return pythonw if os.path.exists(pythonw) else sys.executable


def _ps_quote(text):
    return "'" + str(text).replace("'", "''") + "'"


def shortcut_folder(kind):
    """kind: Desktop, Programs (Start menu) or Startup."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Environment]::GetFolderPath(%s)" % _ps_quote(kind)],
        capture_output=True, text=True, timeout=25)
    return result.stdout.strip()


def shortcut_exists(kind):
    try:
        folder = shortcut_folder(kind)
        return bool(folder) and os.path.exists(
            os.path.join(folder, APP_NAME + ".lnk"))
    except Exception:
        return False


def create_shortcut(kind):
    """Put an Optimus icon on the desktop, Start menu or Startup folder."""
    folder = shortcut_folder(kind)
    if not folder:
        raise RuntimeError("couldn't find the %s folder" % kind)
    icon = make_icon_file()
    script = os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0].endswith(
        ".py") else __file__)
    args = '"%s"' % script
    if kind != "Startup":
        args += " --panel"          # opens the control panel when you click it
    link = os.path.join(folder, APP_NAME + ".lnk")
    command = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut(%s); "
        "$s.TargetPath = %s; $s.Arguments = %s; $s.WorkingDirectory = %s; "
        "$s.IconLocation = %s; $s.Description = 'Optimus voice assistant'; "
        "$s.Save()" % (_ps_quote(link), _ps_quote(launcher_exe()),
                       _ps_quote(args), _ps_quote(BASE_DIR),
                       _ps_quote(icon)))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                            capture_output=True, text=True, timeout=40)
    if result.returncode != 0 or not os.path.exists(link):
        raise RuntimeError((result.stderr or "shortcut was not created")
                           .strip()[:200])
    return link


def remove_shortcut(kind):
    folder = shortcut_folder(kind)
    link = os.path.join(folder, APP_NAME + ".lnk")
    if folder and os.path.exists(link):
        os.remove(link)


# ======================== older copies and old shortcuts ========================
APP_VERSION = "10"


def _is_optimus_script(path, cwd=None):
    try:
        if not os.path.isabs(path) and cwd:
            path = os.path.join(cwd, path)
        with open(path, "rb") as f:
            return b"Optimus" in f.read(8000)
    except Exception:
        return False


def stop_other_copies():
    """Close any older Optimus still running, so only this version is alive."""
    me = os.getpid()
    family = {me}
    try:
        family.update(p.pid for p in psutil.Process(me).parents())
    except Exception:
        pass
    victims = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
        try:
            if proc.info["pid"] in family:
                continue
            name = (proc.info["name"] or "").lower()
            if not name.startswith(("python", "pythonw")):
                continue
            for arg in (proc.info["cmdline"] or [])[1:]:
                if arg.lower().endswith(".py"):
                    base = os.path.basename(arg).lower()
                    if base.startswith(("assistant", "optimus")) and \
                            _is_optimus_script(arg, proc.info.get("cwd")):
                        victims.append(proc)
                    break
        except Exception:
            continue
    for proc in victims:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        psutil.wait_procs(victims, timeout=4)
    except Exception:
        pass
    return len(victims)


def refresh_shortcuts():
    """Point every Optimus shortcut (desktop, Start menu, startup) at this file."""
    script = os.path.abspath(__file__)
    command = (
        "$sh = New-Object -ComObject WScript.Shell; "
        "$dirs = @([Environment]::GetFolderPath('Desktop'), "
        "[Environment]::GetFolderPath('Programs'), "
        "[Environment]::GetFolderPath('Startup'), "
        "[Environment]::GetFolderPath('CommonDesktopDirectory')); "
        "foreach ($d in $dirs) { if (-not $d -or -not (Test-Path $d)) "
        "{ continue }; Get-ChildItem -Path $d -Filter *.lnk -Recurse "
        "-ErrorAction SilentlyContinue | ForEach-Object { try { "
        "$l = $sh.CreateShortcut($_.FullName); "
        "if ($l.Arguments -match '(?i)(assistant|optimus)[^\"\\\\/]*\\.py') { "
        "$l.Arguments = [regex]::Replace($l.Arguments, '\"[^\"]*\\.py\"', "
        "'\"' + %s + '\"'); $l.WorkingDirectory = %s; $l.Save() } } "
        "catch {} } }" % (_ps_quote(script), _ps_quote(BASE_DIR)))
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", command],
                       capture_output=True, text=True, timeout=60)
    except Exception:
        log_problem("refreshing shortcuts")


# ======================== talking to a copy that is already running ========================
IPC_PORT_FILE = os.path.join(BASE_DIR, "ipc_port.txt")
_instance_handle = None
_lock_socket = None
PANEL_LOOK_KEYS = ("panel_accent", "panel_custom", "page_slide",
                   "header_shimmer", "cursor_look", "cursor_style",
                   "mode_colors", "custom_a", "custom_b", "theme")


def log_problem(where, exc_info=None):
    """Write the full error to optimus.log so a silent failure can be read."""
    try:
        import traceback
        text = "".join(traceback.format_exception(*(exc_info or sys.exc_info())))
        with open(os.path.join(BASE_DIR, "optimus.log"), "a",
                  encoding="utf-8") as f:
            f.write("\n[%s] Problem in %s\n%s\n" % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), where, text))
    except Exception:
        pass


def show_message(text, title="Optimus"):
    """A real message box, so you still see it when Optimus has no console."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x40 | 0x40000)
    except Exception:
        print(text)


def already_running():
    """True when another Optimus is running.

    Uses a Windows mutex, which nothing else can block. (The old fixed network
    port could be reserved by Windows after a restart, which made Optimus
    think a copy was already running and quietly quit.)"""
    global _instance_handle, _lock_socket
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.CreateMutexW.restype = ctypes.c_void_p
        _instance_handle = kernel.CreateMutexW(
            None, False, "Local\\OptimusAssistantSingleton10")
        if kernel.GetLastError() == 183:        # ERROR_ALREADY_EXISTS
            return True
    except Exception:
        pass
    try:                       # a free port, remembered in a file
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.bind(("127.0.0.1", 0))
        _lock_socket.listen(4)
        with open(IPC_PORT_FILE, "w") as f:
            f.write(str(_lock_socket.getsockname()[1]))
    except Exception:
        log_problem("starting the panel link")
        _lock_socket = None
    return False


def ipc_server():
    """Lets a second click on the desktop icon open the running Optimus."""
    if _lock_socket is None:
        return
    while True:
        try:
            conn, _ = _lock_socket.accept()
        except Exception:
            time.sleep(1)
            continue
        try:
            conn.settimeout(1.0)
            if conn.recv(64).strip().lower().startswith(b"panel"):
                orb_cmds.put(("panel",))
                conn.sendall(b"ok")
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass


def tell_running_copy(message=b"panel\n"):
    """Ask the running Optimus to open its panel. True if it answered."""
    try:
        with open(IPC_PORT_FILE) as f:
            port = int(f.read().strip())
        with socket.create_connection(("127.0.0.1", port), timeout=3) as c:
            c.sendall(message)
            c.settimeout(3)
            return c.recv(8) == b"ok"
    except Exception:
        return False


def overlay_loop():
    try:
        key = "#010203"
        width, height = 1100, 170
        root = tk.Tk()  # this small window is the orb
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

        def style_window(win):
            win.overrideredirect(True)
            for attr, value in (("-topmost", True),
                                ("-transparentcolor", key)):
                try:
                    win.attributes(attr, value)
                except Exception:
                    pass
            win.configure(bg=key)

        style_window(root)
        fx = OrbFX()
        try:
            cursor_fx = CursorFX(root, key)
        except Exception as error:
            print("Flying cursor unavailable:", error)
            cursor_fx = None
        screen_fx = ScreenFX(root)
        ui = {"size": max(90, min(300, int(settings.get("orb_size",
                                                         ORB_SIZE)))),
              "style": settings.get("orb_style", ORB_STYLE),
              "visible": SHOW_ORB, "drag": None, "moved": False,
              "hover": 0.0, "angle": 0.0, "inside": False, "ripples": [],
              "level": 0.0, "last": time.time(), "frames": 0,
              "error_shown": False, "x": 0, "y": 0, "snap": None,
              "impulse": 0.0, "burst": False}
        if ui["style"] not in ORB_STYLES:
            ui["style"] = "logo"
        if ui["style"] == "logo" and not os.path.exists(current_logo_path()):
            print("No %s found, so the orb uses the reactor look." % ORB_IMAGE)
            ui["style"] = "reactor"
        orb = tk.Canvas(root, width=ui["size"], height=ui["size"], bg=key,
                        highlightthickness=0, cursor="hand2")
        orb.pack()

        def area():
            return work_area() or (0, 0, sw, sh)

        def clamp_pos(x, y):
            s = ui["size"]
            return (max(0, min(sw - s, int(x))), max(0, min(sh - s, int(y))))

        def apply_geometry():
            s = ui["size"] if ui["visible"] else 2
            orb.config(width=s, height=s)
            root.geometry("%dx%d+%d+%d" % (s, s, ui["x"], ui["y"]))

        def default_pos():
            left, top, right, bottom = area()
            return clamp_pos(right - ui["size"] - 8, bottom - ui["size"] - 8)

        def save_pos():
            save_setting("orb_x", ui["x"])
            save_setting("orb_y", ui["y"])

        def reset_pos():
            ui["x"], ui["y"] = default_pos()
            save_pos()
            apply_geometry()

        saved_x, saved_y = settings.get("orb_x"), settings.get("orb_y")
        if saved_x is None or saved_y is None:
            ui["x"], ui["y"] = default_pos()
        else:
            ui["x"], ui["y"] = clamp_pos(saved_x, saved_y)
        apply_geometry()

        def set_style(name):
            ui["style"] = name
            save_setting("orb_style", name)

        def resize(new_size):
            ui["size"] = max(90, min(300, int(new_size)))
            ui["x"], ui["y"] = clamp_pos(ui["x"], ui["y"])
            save_setting("orb_size", ui["size"])
            apply_geometry()

        def on_press(e):
            ui["drag"] = (e.x_root - ui["x"], e.y_root - ui["y"])
            ui["moved"] = False
            ui["snap"] = None

        def on_drag(e):
            if ui["drag"] is None:
                return
            nx, ny = clamp_pos(e.x_root - ui["drag"][0],
                               e.y_root - ui["drag"][1])
            ui["impulse"] -= (nx - ui["x"]) * 0.6
            ui["x"], ui["y"] = nx, ny
            ui["moved"] = True
            root.geometry("+%d+%d" % (ui["x"], ui["y"]))

        def on_release(e):
            if ui["moved"]:
                target = snap_target(ui["x"], ui["y"], ui["size"], area())
                if target != (ui["x"], ui["y"]):
                    ui["snap"] = target
                else:
                    save_pos()
            else:
                ui["burst"] = True
            ui["drag"] = None

        def on_wheel(e):
            resize(ui["size"] + (10 if e.delta > 0 else -10))

        menu = tk.Menu(root, tearoff=0)
        panel = {"obj": None}

        def open_panel():
            """Open the control panel, or bring it to the front."""
            try:
                if panel["obj"] is not None and panel["obj"].alive():
                    panel["obj"].raise_window()
                else:
                    panel["obj"] = ControlPanel(root)
            except Exception:
                log_problem("the control panel")
                try:
                    import shutil as _sh
                    _sh.copyfile(SETTINGS_FILE, SETTINGS_FILE + ".backup")
                except Exception:
                    pass
                for _k in PANEL_LOOK_KEYS:
                    settings.pop(_k, None)
                try:
                    save_setting("_reset_look", time.time())
                    panel["obj"] = ControlPanel(root)
                except Exception:
                    log_problem("the control panel (second try)")
                    show_message("The control panel could not open.\n\n"
                                 "The details were saved in optimus.log next "
                                 "to the program. Please send that file.")

        def on_right(e):
            menu.delete(0, "end")
            menu.add_command(label="Wake Optimus",
                             command=lambda: wake_queue.put("wake"))
            menu.add_command(label="Control panel...", command=open_panel)
            menu.add_command(label="Stop speaking", command=stop_speaking)
            menu.add_command(
                label="Flying cursor "
                + ("on" if settings.get("cursor_style", "Hero Cursor") == "Off"
                   else "off"), command=toggle_flier)
            menu.add_command(label="Unmute" if state["muted"] else "Mute",
                             command=toggle_mute_state)
            menu.add_command(
                label="Voice lock " + ("off" if lock_enabled() else "on"),
                command=toggle_lock_state)
            styles = tk.Menu(menu, tearoff=0)
            for name in ORB_STYLES:
                styles.add_command(label=name.title(),
                                   command=lambda n=name: set_style(n))
            menu.add_cascade(label="Orb style", menu=styles)
            menu.add_command(label="Reset orb position", command=reset_pos)
            menu.add_separator()
            menu.add_command(label="Quit Optimus",
                             command=lambda: os._exit(0))
            try:
                root.focus_force()
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()

        orb.bind("<ButtonPress-1>", on_press)
        orb.bind("<B1-Motion>", on_drag)
        orb.bind("<ButtonRelease-1>", on_release)
        orb.bind("<Double-Button-1>", lambda e: wake_queue.put("wake"))
        orb.bind("<Button-3>", on_right)
        orb.bind("<MouseWheel>", on_wheel)

        sub = tk.Toplevel(root)  # this one shows the subtitles
        style_window(sub)
        canvas = tk.Canvas(sub, width=width, height=height, bg=key,
                           highlightthickness=0)
        canvas.pack()
        font = (SUBTITLE_FONT, SUBTITLE_SIZE)
        shadow = canvas.create_text(width // 2 + 2, height - 8, text="",
                                    anchor="s", width=width - 80,
                                    justify="center", font=font,
                                    fill="#00080c")
        main = canvas.create_text(width // 2, height - 10, text="",
                                  anchor="s", width=width - 80,
                                  justify="center", font=font,
                                  fill=SUBTITLE_COLOR)
        sub.withdraw()
        st = {"type": None, "hide": None, "full": ""}

        def cancel(name):
            if st[name]:
                try:
                    root.after_cancel(st[name])
                except Exception:
                    pass
                st[name] = None

        def set_text(t):
            canvas.itemconfig(shadow, text=t)
            canvas.itemconfig(main, text=t)

        def place():
            left, top, right, bottom = area()
            x = (left + right - width) // 2
            y = bottom - height - 12
            sub.geometry("%dx%d+%d+%d" % (width, height, x, y))

        def type_out(i, per_tick):
            full = st["full"]
            i = min(len(full), i + per_tick)
            set_text(full[:i])
            if i < len(full):
                st["type"] = root.after(40, type_out, i, per_tick)
            else:
                st["type"] = None

        def process_orb_commands():
            while True:
                try:
                    cmd = orb_cmds.get_nowait()
                except queue.Empty:
                    break
                if cmd[0] == "style":
                    set_style(cmd[1])
                elif cmd[0] == "size":
                    resize(ui["size"] + cmd[1])
                elif cmd[0] == "reset":
                    reset_pos()
                elif cmd[0] == "visible":
                    ui["visible"] = bool(cmd[1])
                    apply_geometry()
                elif cmd[0] == "logo":
                    fx.base = None          # reload the newly chosen logo
                    fx.base_failed = False
                    fx.cache.clear()
                    set_style("logo")
                elif cmd[0] == "size_to":
                    resize(cmd[1])
                elif cmd[0] == "panel":
                    open_panel()
                elif cmd[0] == "assemble":
                    screen_fx.play(cmd[1])
                elif cmd[0] == "alpha":
                    try:
                        root.attributes("-alpha", max(0.3, min(1.0, cmd[1])))
                    except Exception:
                        pass

        def draw_frame(now, dt):
            size = ui["size"]
            mode = orb_state["mode"]
            px, py = root.winfo_pointerxy()
            cx = ui["x"] + size / 2.0
            cy = ui["y"] + size / 2.0
            dx, dy = px - cx, py - cy
            dist = math.hypot(dx, dy)
            near = max(0.0, 1.0 - dist / (size * 1.6))
            ui["hover"] += (near - ui["hover"]) * 0.18
            entered = dist < size * 0.5 and not ui["inside"]
            if entered:
                ui["inside"] = True
            elif dist > size * 0.75:
                ui["inside"] = False
            level = orb_state.get("level", 0.0)
            if now < orb_state.get("demo_until", 0.0):
                mode = "speaking"
                level = 0.05 + 0.13 * abs(math.sin(now * 5.3)) * (
                    0.6 + 0.4 * math.sin(now * 2.1))
            if mode == "listening":
                target = min(1.0, level * 6.0)
            elif mode == "speaking":
                target = min(1.0, level * 3.0)
            else:
                target = 0.0
            ui["level"] += (target - ui["level"]) * 0.35
            style = ui["style"]
            if style == "logo":
                if fx.base is None and not fx.base_failed:
                    try:
                        fx.base = prepare_logo(current_logo_path())
                    except Exception as error:
                        print("Orb logo unavailable:", error)
                        fx.base_failed = True
                if fx.base is not None:
                    if entered:
                        fx.rings.append((now, 0.6))
                        fx.wobble_v += random.choice((-1, 1)) * 35
                    if ui["burst"]:
                        ui["burst"] = False
                        fx_burst(fx, size, now)
                    if ui["impulse"]:
                        fx.wobble_v += ui["impulse"] * 15
                        ui["impulse"] = 0.0
                    orb.delete("all")
                    draw_logo_orb(orb, fx, size, now, dt, mode, ui["hover"],
                                  ui["level"], dx, dy, dist, px - ui["x"],
                                  py - ui["y"], key)
                    return
                style = "reactor"
            base_color = ORB_COLORS.get(mode, ORB_COLORS["idle"])
            if entered:
                ui["ripples"].append(now)
            ui["ripples"] = [t0 for t0 in ui["ripples"] if now - t0 < 0.9]
            speed = {"idle": 25, "listening": 80, "thinking": 220,
                     "speaking": 120, "muted": 0}.get(mode, 25)
            ui["angle"] = (ui["angle"]
                           + (speed + ui["hover"] * 140) * dt) % 360
            rate = {"speaking": 7.0, "listening": 4.0,
                    "thinking": 5.0}.get(mode, 1.3)
            pulse = (math.sin(now * rate) + 1) / 2
            if mode in ("listening", "speaking"):
                pulse = max(pulse * 0.4, ui["level"])
            if mode == "muted":
                pulse = 0.0
            color = mix_color(base_color, "#ffffff", ui["hover"] * 0.3)
            look = (0.0, 0.0)
            if dist > 1 and ui["hover"] > 0.02:
                k = min(size * 0.06, dist / 25.0) * ui["hover"]
                look = (dx / dist * k, dy / dist * k)
            orb.delete("all")
            if style == "hud":
                draw_hud(orb, size, color, ui["hover"], ui["angle"], pulse,
                         look)
            elif style == "pulse":
                draw_pulse(orb, size, color, ui["hover"], ui["angle"],
                           pulse, look)
            else:
                draw_reactor(orb, size, color, ui["hover"], ui["angle"],
                             pulse, look)
            for t0 in ui["ripples"]:
                age = now - t0
                r = size * 0.30 + age * size * 0.55
                orb.create_oval(size / 2.0 - r, size / 2.0 - r,
                                size / 2.0 + r, size / 2.0 + r,
                                outline=mix_color(color, key, age / 0.9),
                                width=2)

        def animate():
            try:
                now = time.time()
                dt = min(0.1, now - ui["last"])
                ui["last"] = now
                process_orb_commands()
                ui["frames"] += 1
                if ui["frames"] % 150 == 0:
                    root.attributes("-topmost", True)
                if ui["snap"] is not None:
                    tx, ty = ui["snap"]
                    nx = ui["x"] + (tx - ui["x"]) * 0.3
                    ny = ui["y"] + (ty - ui["y"]) * 0.3
                    if abs(tx - nx) < 1.5 and abs(ty - ny) < 1.5:
                        nx, ny = tx, ty
                        ui["snap"] = None
                        fx.scale_v += 2.0
                    ui["x"], ui["y"] = int(round(nx)), int(round(ny))
                    root.geometry("+%d+%d" % (ui["x"], ui["y"]))
                    if ui["snap"] is None:
                        save_pos()
                if ui["visible"]:
                    draw_frame(now, dt)
            except Exception as error:
                if not ui["error_shown"]:
                    ui["error_shown"] = True
                    print("Orb problem:", error)
            root.after(33, animate)

        def poll():
            try:
                while True:
                    kind, value, seconds = subtitle_queue.get_nowait()
                    if kind == "show":
                        cancel("hide")
                        cancel("type")
                        st["full"] = value
                        sub.deiconify()
                        place()
                        if seconds and len(value) > 3:
                            ticks = max(1, int(seconds * 1000 / 40))
                            per_tick = max(1, -(-len(value) // ticks))
                            set_text("")
                            type_out(0, per_tick)
                        else:
                            set_text(value)
                    else:
                        cancel("type")
                        cancel("hide")
                        set_text(st["full"])
                        st["hide"] = root.after(value, sub.withdraw)
            except queue.Empty:
                pass
            root.after(60, poll)

        def optimus_areas():
            rects = []
            for win in (root, panel["obj"].win if panel["obj"] is not None
                        and panel["obj"].alive() else None):
                try:
                    if win is not None and win.winfo_viewable():
                        rects.append((win.winfo_rootx(), win.winfo_rooty(),
                                      win.winfo_width(), win.winfo_height()))
                except Exception:
                    pass
            return rects

        if cursor_fx is not None:
            cursor_fx.areas = optimus_areas
        fly = {"last": time.time(), "error": False}

        def fly_tick():
            try:
                now = time.time()
                dt = min(0.06, now - fly["last"])
                fly["last"] = now
                if cursor_fx is not None:
                    cursor_fx.update(now, dt)
            except Exception as error:
                if not fly["error"]:
                    fly["error"] = True
                    print("Flying cursor problem:", error)
            root.after(22, fly_tick)

        animate()
        poll()
        fly_tick()
        try:
            root.attributes("-alpha", max(0.3, min(1.0, float(
                settings.get("orb_opacity", 1.0)))))
        except Exception:
            pass
        if settings.get("startup_fx"):
            root.after(2500, lambda: screen_fx.play(None))
        if "--panel" in sys.argv or settings.get("open_panel_on_start"):
            root.after(1200, open_panel)
        root.mainloop()
    except Exception as error:
        print("Subtitles unavailable:", error)


# ======================== voice out (pipelined) ========================
def key_down(vk):
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def ptt_pressed():
    vk = ptt_vk()
    return bool(vk) and key_down(vk)


def chat_event(kind, text):
    """Tell any open control panel about a new line in the conversation."""
    item = (kind, text)
    chat_history.append(item)
    for listener in list(chat_listeners):
        try:
            listener.put_nowait(item)
        except Exception:
            pass


def log_event(kind, text):
    chat_event(kind, text)
    try:
        if (os.path.exists(HISTORY_LOG)
                and os.path.getsize(HISTORY_LOG) > 1000000):
            os.replace(HISTORY_LOG, HISTORY_LOG + ".old")
        with open(HISTORY_LOG, "a", encoding="utf-8") as f:
            f.write("[%s] %s: %s\n" % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kind, text))
    except Exception:
        pass


def say(text):
    """Queue a sentence to be spoken. Returns immediately."""
    text = clean(text)
    if text:
        print("Optimus:", text)
        log_event("Optimus", text)
        if not state.get("quiet"):      # quiet = a typed command, text only
            speech_queue.put((speak_gen["n"], text))


def stop_speaking():
    """Cut off whatever Optimus is saying right now."""
    speak_gen["n"] += 1
    stop_epoch["n"] += 1   # also tells any answer still being written to stop
    try:
        sd.stop()
    except Exception:
        pass
    for q in (speech_queue, audio_queue):
        while True:
            try:
                q.get_nowait()
                q.task_done()
            except queue.Empty:
                break
    hide_subtitle(300)


def wait_speech():
    """Wait until everything queued has been spoken."""
    speech_queue.join()
    audio_queue.join()
    time.sleep(0.45)   # let the speaker's echo die before the mic opens


def interrupted():
    """True if the user cut Optimus off since the current command began."""
    return stop_epoch["n"] != reply_epoch["n"]


def say_stream(sentences):
    """Speak an answer as it is written, and stop writing it if interrupted.

    The first sentence is spoken straight away. After that, short sentences
    are joined so the voice keeps one natural flow instead of many tiny,
    choppy clips."""
    pending = ""
    first = True
    for sentence in sentences:
        if interrupted():
            break
        sentence = clean(sentence)
        if not sentence:
            continue
        if first:
            say(sentence)
            first = False
            continue
        pending = (pending + " " + sentence).strip()
        if len(pending) >= 90:
            say(pending)
            pending = ""
    else:
        if pending and not interrupted():
            say(pending)
    try:
        sentences.close()   # closes the connection so the AI stops generating
    except Exception:
        pass


def speech_busy():
    return (working["on"] or speech_queue.unfinished_tasks > 0
            or audio_queue.unfinished_tasks > 0)


def interrupt_watcher():
    """Tap the push-to-talk key at ANY moment to cut Optimus off."""
    was_down = False
    while True:
        down = ptt_pressed()
        if down and not was_down and speech_busy():
            stop_speaking()
        was_down = down
        time.sleep(0.03)


def current_style():
    style = settings.get("voice_style", VOICE_STYLE)
    if style not in VOICE_STYLES:
        style = "jarvis"
    try:     # a voice your voice file doesn't have would sound random
        have = set(tts.get_voices()) if tts is not None else None
        if have and VOICE_STYLES[style][0] not in have:
            for name, spec in VOICE_STYLES.items():
                if spec[0] in have:
                    return name
    except Exception:
        pass
    return style


def apply_voice_effects(samples, rate, style):
    """Voice effects: overlord (villain), droid (robot), radio, deep."""
    effect = style
    if effect not in ("overlord", "droid", "radio", "deep"):
        return samples
    samples = np.asarray(samples, dtype=np.float32)
    if effect == "deep":
        n = int(len(samples) / 0.86)
        low = np.interp(np.linspace(0, len(samples) - 1, n),
                        np.arange(len(samples)), samples).astype(np.float32)
        return low
    if effect == "droid":
        t = np.arange(len(samples), dtype=np.float32) / float(rate)
        ring = samples * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 70 * t)))
        crushed = np.round(ring * 24.0) / 24.0
        peak = float(np.max(np.abs(crushed))) or 1.0
        return (crushed / peak * 0.9).astype(np.float32)
    if effect == "radio":
        spectrum = np.fft.rfft(samples)
        freqs = np.fft.rfftfreq(len(samples), 1.0 / rate)
        spectrum[(freqs < 350) | (freqs > 3300)] = 0
        band = np.fft.irfft(spectrum, len(samples)).astype(np.float32)
        band = np.tanh(band * 3.0) / np.tanh(3.0)
        noise = np.random.normal(0, 0.012, len(band)).astype(np.float32)
        peak = float(np.max(np.abs(band))) or 1.0
        return (band / peak * 0.9 + noise).astype(np.float32)
    factor = 0.80   # overlord
    n = int(len(samples) / factor)
    low = np.interp(np.linspace(0, len(samples) - 1, n),
                    np.arange(len(samples)), samples).astype(np.float32)
    delay = max(1, int(rate * 0.012))
    ring = low.copy()
    ring[delay:] += 0.35 * low[:-delay]
    grit = np.tanh(ring * 2.2) / np.tanh(2.2)
    echo = int(rate * 0.09)
    out = np.zeros(len(grit) + echo, dtype=np.float32)
    out[:len(grit)] += grit
    out[echo:] += 0.25 * grit
    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * 0.92).astype(np.float32)


def synth_worker():
    if tts is not None:
        try:
            tts.create("Ready.", voice=VOICE, speed=VOICE_SPEED,
                       lang="en-gb")
        except Exception:
            pass
    while True:
        gen, text = speech_queue.get()
        try:
            if gen != speak_gen["n"]:
                continue
            if tts is not None:
                style = current_style()
                voice, lang, speed = VOICE_STYLES[style]
                effect = VOICE_PACKS[style][3]
                speed = speed * float(settings.get("voice_speed", 1.0))
                spoken = speakable(text) or text
                try:
                    samples, rate = tts.create(spoken, voice=voice,
                                               speed=speed, lang=lang)
                except Exception as error:
                    print("Voice %s failed (%s), trying a backup voice"
                          % (voice, error))
                    if style == "friendly":
                        backup = ("af_sarah", "en-us")
                    else:
                        backup = (VOICE, "en-gb")
                    samples, rate = tts.create(spoken, voice=backup[0],
                                               speed=VOICE_SPEED,
                                               lang=backup[1])
                    effect = ""
                samples = apply_voice_effects(samples, rate, effect)
                # A short breath between sentences, so it doesn't sound like
                # clips glued together.
                samples = np.concatenate([
                    np.asarray(samples, dtype=np.float32),
                    np.zeros(int(rate * 0.15), dtype=np.float32)])
                audio_queue.put((gen, text, samples, rate))
            else:
                audio_queue.put((gen, text, None, 0))
        except Exception as error:
            print("Voice error:", error)
            audio_queue.put((gen, text, None, 0))
        finally:
            speech_queue.task_done()


def start_barge_monitor():
    """Headphone mode: watch the mic while Optimus talks."""
    if not headphones_on():
        return None
    holder = {"level": 0.0}

    def callback(indata, frames, time_info, status):
        holder["level"] = float(np.sqrt(np.mean(indata ** 2)))

    try:
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                dtype="float32", callback=callback)
        stream.start()
        holder["stream"] = stream
        return holder
    except Exception:
        return None


def stop_barge_monitor(holder):
    if holder and holder.get("stream"):
        try:
            holder["stream"].stop()
            holder["stream"].close()
        except Exception:
            pass


def play_worker():
    try:
        import comtypes
        comtypes.CoInitialize()
    except Exception:
        pass
    while True:
        gen, text, samples, rate = audio_queue.get()
        try:
            if gen != speak_gen["n"]:
                continue
            set_orb("speaking")
            if samples is not None:
                show_subtitle(text, len(samples) / rate * 0.85)
                try:
                    sd.play(samples, rate, latency="high")   # steadier
                except TypeError:
                    sd.play(samples, rate)
                started = time.time()
                end = started + len(samples) / rate + 0.2
                monitor = start_barge_monitor()
                loud_count = 0
                key_count = 0
                interrupted = False
                while time.time() < end:
                    idx = int((time.time() - started) * rate)
                    chunk = samples[idx:idx + 1200]
                    orb_state["level"] = (
                        float(np.sqrt(np.mean(chunk ** 2)))
                        if len(chunk) else 0.0)
                    if gen != speak_gen["n"]:
                        interrupted = True
                        break
                    key_count = key_count + 1 if ptt_pressed() else 0
                    if key_count >= 3:
                        print("Speech stopped: the talk key was pressed.")
                        stop_speaking()
                        interrupted = True
                        break
                    if (monitor is not None and monitor["level"]
                            > max(THRESHOLD * 2.0, 0.05)):
                        loud_count += 1
                        if loud_count >= 8:
                            print("Speech stopped: headphone mode heard a "
                                  "voice.")
                            if time.time() - started < 3.0:
                                # cut off almost at once: the mic is hearing
                                # Optimus through the speakers, so switch the
                                # mode off instead of silencing every answer
                                save_setting("headphones", False)
                                print("Headphone mode turned off (it only "
                                      "works with headphones).")
                            stop_speaking()
                            interrupted = True
                            break
                    else:
                        loud_count = 0
                    time.sleep(0.04)
                stop_barge_monitor(monitor)
                if interrupted:
                    sd.stop()
                else:
                    sd.wait()
            else:
                show_subtitle(text)
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            hide_subtitle()
            last_spoken_at["t"] = time.time()
        except Exception as error:
            print("Playback error:", error)
        finally:
            audio_queue.task_done()


def farewell():
    hour = datetime.now().hour
    pool = FAREWELLS_NIGHT if (hour >= 21 or hour < 5) else FAREWELLS_DAY
    return random.choice(pool).format(n=USER_NAME)


def greeting():
    hour = datetime.now().hour
    part = ("morning" if 5 <= hour < 12
            else "afternoon" if 12 <= hour < 17 else "evening")
    options = [
        "Good %s, %s! Welcome back. How is your day going?"
        % (part, USER_NAME),
        "Welcome back, %s! Optimus is online and ready. How is your day "
        "going so far?" % USER_NAME,
        "Hello %s, welcome back! It's so good to see you. How are you doing "
        "today?" % USER_NAME,
    ]
    return random.choice(options)


# ======================== voice in ========================
# ======================== accuracy helpers ========================
def normalize_audio(audio):
    """Lift quiet recordings to a healthy level before recognising them."""
    audio = np.asarray(audio, dtype=np.float32)
    if len(audio) == 0:
        return audio
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-4:
        return audio
    gain = min(0.85 / peak, 6.0)   # 12x used to blow background noise up
    return audio * gain if gain > 1.0 else audio


def read_vocab():
    try:
        with open(VOCAB_FILE, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()][:60]
    except Exception:
        return []


def vocab_prompt():
    words = read_vocab()
    if not words:
        return PROMPT
    return PROMPT + " " + ", ".join(words) + "."


def vocab_command(t, words):
    m = (re.match(r"^add\s+(.+?)\s+to\s+(?:your |my |the )?vocabulary$", t)
         or re.match(r"^(?:learn|remember)(?: the)? (?:word|name|term)\s+(.+)$",
                     t))
    if m:
        word = m.group(1).strip()
        with open(VOCAB_FILE, "a", encoding="utf-8") as f:
            f.write(word + "\n")
        return "Added %s to my vocabulary." % word
    if t in ("clear your vocabulary", "clear my vocabulary"):
        try:
            os.remove(VOCAB_FILE)
        except Exception:
            pass
        return "Vocabulary cleared."
    return None


def select_microphone():
    """Use a specific microphone if MIC_DEVICE_NAME is set."""
    if not MIC_DEVICE_NAME:
        return
    try:
        for index, device in enumerate(sd.query_devices()):
            if (device["max_input_channels"] > 0
                    and MIC_DEVICE_NAME.lower() in device["name"].lower()):
                sd.default.device = (index, sd.default.device[1])
                print("Using microphone:", device["name"])
                return
        print("Microphone '%s' not found, using the default."
              % MIC_DEVICE_NAME)
    except Exception as error:
        print("Could not select the microphone:", error)


def mic_check():
    say("Microphone check. Please speak normally for three seconds.")
    wait_speech()
    set_orb("listening")
    audio = sd.rec(int(3 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1,
                   dtype="float32")
    sd.wait()
    audio = audio.flatten()
    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))
    try:
        name = sd.query_devices(kind="input")["name"]
    except Exception:
        name = "your microphone"
    print("Mic check: device=%s rms=%.4f peak=%.3f threshold=%.4f"
          % (name, rms, peak, THRESHOLD))
    if peak < 0.05:
        advice = ("I can barely hear you. Raise the microphone volume in "
                  "Windows sound settings, or move closer.")
    elif peak > 0.98:
        advice = ("That's clipping. Lower the microphone volume a little.")
    elif rms < THRESHOLD * 1.5:
        advice = ("You're quiet compared with the room noise. Move closer or "
                  "speak up a little.")
    else:
        advice = "I hear you loud and clear."
    return "I'm listening through %s. %s" % (name, advice)


# ======================== keeping the offline brain alive ========================
def ollama_up():
    try:
        http_get("http://localhost:11434/", timeout=2)
        return True
    except Exception:
        return False


def find_ollama():
    candidates = [shutil.which("ollama"),
                  os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs",
                               "Ollama", "ollama.exe")]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def ensure_ollama(wait=25):
    """Make sure the offline brain is running, starting it if it isn't."""
    with ollama_lock:
        if ollama_up():
            return True
        exe = find_ollama()
        if not exe:
            return False
        try:
            subprocess.Popen([exe, "serve"], creationflags=0x08000000,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except Exception as error:
            print("Could not start Ollama:", error)
            return False
        deadline = time.time() + wait
        while time.time() < deadline:
            if ollama_up():
                return True
            time.sleep(1)
        return False


def open_ollama(request, timeout):
    """Open a request to Ollama, waking it up once if it is not running."""
    try:
        return urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError:
        if ensure_ollama():
            return urllib.request.urlopen(request, timeout=timeout)
        raise


def brain_status():
    if ollama_up():
        return "My offline brain is running fine, %s." % USER_NAME
    say("My offline brain is asleep. Let me wake it.")
    if ensure_ollama():
        return "It's awake again."
    return ("I couldn't start it. Please open the Ollama app from the Start "
            "menu.")


def ollama_watchdog():
    while True:
        time.sleep(60)
        try:
            if not ollama_up():
                print("Offline brain is down, restarting it")
                ensure_ollama()
        except Exception as error:
            print("Brain watchdog problem:", error)


def wait_for_microphone(max_wait=90):
    """At start-up Windows can take a while to bring the microphone online."""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            sd._terminate()
            sd._initialize()
            if any(d["max_input_channels"] > 0 for d in sd.query_devices()):
                return True
        except Exception as error:
            print("Waiting for the microphone:", error)
        time.sleep(3)
    return False


def calibrate(seconds=2.0):
    time.sleep(0.6)   # let the speaker's echo and any click die away first
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    block = int(0.1 * SAMPLE_RATE)
    levels = sorted(float(np.sqrt(np.mean(audio[i:i + block] ** 2)))
                    for i in range(0, len(audio) - block, block))
    # Judge the room by its quietest half, so one loud moment (fan spinning
    # up, a click, the tail of Optimus's own voice) cannot wreck the setting.
    quiet = levels[:max(1, len(levels) // 2)]
    noise = float(np.mean(quiet)) if quiet else 0.01
    return min(max(noise * 2.5, 0.012), 0.05)


def record_until_silence(max_seconds=12, silence_seconds=None,
                         wait_seconds=None, interrupt=None):
    if silence_seconds is None:
        silence_seconds = END_SILENCE
    block = int(0.1 * SAMPLE_RATE)
    pre = collections.deque(maxlen=5)
    audio = []
    started = False
    quiet = 0
    waited = 0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="float32") as stream:
        while True:
            data, _ = stream.read(block)
            data = data.flatten()
            rms = float(np.sqrt(np.mean(data ** 2)))
            orb_state["level"] = rms
            loud = rms > THRESHOLD
            if not started:
                pre.append(data)
                if loud:
                    started = True
                    set_orb("listening")
                    audio = list(pre)
                else:
                    waited += 1
                    if interrupt and interrupt():
                        return None
                    if wait_seconds and waited >= int(wait_seconds / 0.1):
                        return None
                continue
            audio.append(data)
            quiet = 0 if loud else quiet + 1
            if (quiet >= int(silence_seconds / 0.1)
                    or len(audio) >= int(max_seconds / 0.1)):
                break
    audio = np.concatenate(audio)
    return audio if len(audio) > 0.4 * SAMPLE_RATE else None


def record_while_key(vk, max_seconds=30):
    """Push-to-talk: record for as long as the key is held down."""
    block = int(0.1 * SAMPLE_RATE)
    audio = []
    set_orb("listening")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="float32") as stream:
        while key_down(vk) and len(audio) < int(max_seconds / 0.1):
            data, _ = stream.read(block)
            audio.append(data.flatten())
    if not audio:
        return None
    audio = np.concatenate(audio)
    return audio if len(audio) > 0.4 * SAMPLE_RATE else None


def transcribe(m, audio, prompt=None, beam=None, strict=True):
    """Returns (clean lowercase text, original text with punctuation).

    strict=True throws away speech Whisper itself is unsure about, so
    Optimus says nothing instead of acting on a wrong guess.
    """
    if prompt is None:
        prompt = vocab_prompt()
    voiced = 1.0
    try:
        raw_audio = np.asarray(audio, dtype=np.float32)
        step = int(0.1 * SAMPLE_RATE)
        count = len(raw_audio) // step
        if count:
            levels = np.sqrt(np.mean(
                raw_audio[:count * step].reshape(count, step) ** 2, axis=1))
            voiced = float(np.mean(levels > THRESHOLD * 0.8))
    except Exception:
        pass
    if strict and voiced < 0.2:
        print("(ignored a noise, not speech)")
        return "", ""
    scores = []
    segments, _ = m.transcribe(
        normalize_audio(audio), language=SPEECH_LANGUAGE,
        beam_size=beam or BEAM,
        vad_filter=True, temperature=0.0, condition_on_previous_text=False,
        without_timestamps=True, initial_prompt=prompt)
    kept = []
    for s in segments:
        score = getattr(s, "avg_logprob", 0.0)
        if strict and (score < MIN_CONFIDENCE
                       or (getattr(s, "no_speech_prob", 0.0) > 0.6
                           and score < -0.8)):
            print("(ignored unclear speech: %r, confidence %.2f)"
                  % (s.text.strip(), score))
            continue
        kept.append(s.text.strip())
        scores.append(score)
    raw = " ".join(kept).strip()
    text = re.sub(r"[^\w\s]", " ", raw.lower())
    text = " ".join(text.split())
    if text in HALLUCINATIONS:
        return "", ""
    if strict and text in SOCIAL_PHRASES:
        recent = time.time() - last_spoken_at["t"] < 25
        best = max(scores) if scores else -9.0
        if not (recent and voiced >= 0.35 and best > -0.7):
            print("(ignored %r: probably not really said)" % text)
            return "", ""
    if strict:
        # Whisper sometimes just parrots its prompt back on noisy audio.
        prompt_words = set(re.sub(r"[^\w\s]", " ", prompt.lower()).split())
        heard = text.split()
        if len(heard) >= 3 and all(w in prompt_words for w in heard):
            return "", ""
    return text, raw


def load_whisper():
    """Use the graphics card if it works, otherwise the CPU."""
    global BEAM
    if USE_GPU and not os.path.exists(GPU_FLAG):
        open(GPU_FLAG, "w").close()
        try:
            m = WhisperModel(WHISPER_MODEL, device="cuda",
                             compute_type="int8_float16")
            segments, _ = m.transcribe(np.zeros(SAMPLE_RATE, dtype="float32"),
                                       language="en")
            list(segments)
            os.remove(GPU_FLAG)
            BEAM = 4   # the GPU is fast enough to double-check its hearing
            print("Speech recognition running on the GPU")
            return m
        except Exception as error:
            print("GPU not available, using the CPU:", error)
            try:
                os.remove(GPU_FLAG)
            except Exception:
                pass
    elif USE_GPU:
        print("The GPU failed last time, so using the CPU. "
              "Delete gpu_loading.flag to try the GPU again.")
    BEAM = 1
    print("Speech recognition running on the CPU")
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")


# ======================== apps, folders, files ========================
def ps_json(command):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + command],
            capture_output=True, text=True, encoding="utf-8")
        out = result.stdout.strip()
        if not out:
            return []
        data = json.loads(out)
        return data if isinstance(data, list) else [data]
    except Exception:
        return []


def load_apps():
    apps = {}
    for item in ps_json("Get-StartApps | ConvertTo-Json"):
        apps[norm(item["Name"])] = (item["Name"], item["AppID"])
    apps.pop("", None)
    return apps


def build_index():
    roots = [HOME] + [c + ":\\" for c in "DEFGH"
                      if os.path.exists(c + ":\\")]
    folders, files = {}, {}
    count = 0
    for root in roots:
        top = root.rstrip("\\")
        for dirpath, dirnames, filenames in os.walk(root):
            rel = dirpath[len(top):].strip("\\")
            depth = 0 if rel == "" else rel.count("\\") + 1
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".")
                           and d.lower() not in SKIP_FOLDERS]
            if depth >= MAX_DEPTH:
                dirnames[:] = []
            for d in dirnames:
                folders[norm(d)] = os.path.join(dirpath, d)
            for f in filenames:
                files[norm(os.path.splitext(f)[0])] = os.path.join(dirpath, f)
            count += len(dirnames) + len(filenames)
            if count > MAX_INDEX:
                break
        if count > MAX_INDEX:
            break
    folders.pop("", None)
    files.pop("", None)
    return folders, files


def load_cache():
    global FOLDERS, FILES
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        FOLDERS, FILES = data["folders"], data["files"]
    except Exception:
        pass


def refresh_index():
    global FOLDERS, FILES
    folders, files = build_index()
    FOLDERS, FILES = folders, files
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"folders": folders, "files": files}, f)
    except Exception:
        pass
    print("Index ready:", len(folders), "folders,", len(files), "files")


def find_best(name, table):
    key = norm(name)
    if len(key) < 2 or not table:
        return None
    if key in table:
        return table[key]
    contains = [k for k in table if key in k]
    if contains:
        return table[min(contains, key=len)]
    if fuzz_process is not None:
        found = fuzz_process.extractOne(key, list(table), scorer=fuzz.ratio,
                                        score_cutoff=70)
        return table[found[0]] if found else None
    if len(table) <= 20000:
        close = difflib.get_close_matches(key, list(table), n=1, cutoff=0.7)
        return table[close[0]] if close else None
    return None


# Real words that look a lot like "optimus" but are not the wake word.
NOT_WAKE = {"optimum", "optimums", "optimal", "optimally", "optimism",
            "optimist", "optimists", "optimistic", "optimize", "optimise",
            "optimized", "optimised", "optimizing", "optimising",
            "optimizer", "optimization", "optimisation"}


def find_wake_word(words):
    for i, w in enumerate(words):
        if w in NOT_WAKE:
            continue
        if (w == WAKE_WORD
                or difflib.SequenceMatcher(None, w, WAKE_WORD).ratio() >= 0.8):
            return i
    return -1


def open_drive(words):
    i = words.index("drive")
    spoken = words[i - 1] if i > 0 else ""
    letter = LETTERS.get(spoken)
    if not letter:
        return "Which drive?"
    path = letter.upper() + ":\\"
    if not os.path.exists(path):
        return "I can't find drive " + letter.upper()
    os.startfile(path)
    return "Opening drive " + letter.upper()


def open_target(words):
    if not words:
        return "Open what?"
    if "drive" in words:
        return open_drive(words)
    kind = None
    if words[0] in ("folder", "file"):
        kind, words = words[0], words[1:]
    elif words[-1] in ("folder", "file"):
        kind, words = words[-1], words[:-1]
    name = " ".join(words)
    key = norm(name)
    if not key:
        return "Open what?"
    if kind != "file" and key in SPECIAL_FOLDERS:
        os.startfile(SPECIAL_FOLDERS[key])
        return "Opening " + name
    if kind is None:
        app = find_best(name, APPS)
        if app:
            subprocess.Popen(["explorer.exe",
                              "shell:AppsFolder\\" + app[1]])
            return "Opening " + app[0]
        if key in WEBSITES:
            webbrowser.open(WEBSITES[key])
            return "Opening " + name
    path = None
    if kind != "file":
        path = find_best(name, FOLDERS)
    if not path and kind != "folder":
        path = find_best(name, FILES)
    if path:
        os.startfile(path)
        return "Opening " + name
    if not FOLDERS and not FILES:
        return "I'm still learning where your files are. Try again in a minute."
    return "I could not find " + name


def close_app(words):
    name = " ".join(words)
    key = norm(name)
    if not key:
        return "Close what?"
    procs = ps_json("Get-Process | Where-Object "
                    "{$_.MainWindowTitle -ne ''} | Select-Object "
                    "Id,ProcessName,MainWindowTitle | ConvertTo-Json")
    me = os.getpid()
    matches = [p for p in procs if p["Id"] != me and
               (key in norm(p["ProcessName"]) or
                key in norm(p["MainWindowTitle"]))]
    if not matches:
        names = {norm(p["ProcessName"]): p for p in procs}
        close = difflib.get_close_matches(key, list(names), n=1,
                                          cutoff=0.7)
        matches = [names[close[0]]] if close else []
    if not matches:
        return "I can't find " + name + " running"
    matches = [p for p in matches
               if p["ProcessName"].lower() not in PROTECTED]
    if not matches:
        return "I can't close that one"
    for p in matches:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process -Id %d).CloseMainWindow()" % p["Id"]],
                       capture_output=True)
    return "Closing " + name


# ======================== window control ========================
# Minimize and close work on real window handles, and CHECK the result, so
# Optimus only says "closed" when the window really went away.
WINDOW_FILLER = {"the", "this", "that", "current", "active", "window",
                 "windows", "application", "app", "program", "properly",
                 "please", "it", "one", "now", "completely", "fully",
                 "my", "screen"}
APP_NICE_NAMES = {"msedge": "Edge", "code": "VS Code", "winword": "Word",
                  "excel": "Excel", "powerpnt": "PowerPoint",
                  "explorer": "File Explorer", "whatsapp": "WhatsApp",
                  "chrome": "Chrome", "spotify": "Spotify"}
_u32 = {}


def user32_api():
    """A private, carefully typed handle to the Windows window functions."""
    if not _u32:
        import ctypes.wintypes as wt
        u = ctypes.WinDLL("user32", use_last_error=True)
        u.IsWindowVisible.argtypes = [wt.HWND]
        u.IsWindow.argtypes = [wt.HWND]
        u.IsIconic.argtypes = [wt.HWND]
        u.GetWindowTextLengthW.argtypes = [wt.HWND]
        u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
        u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
        u.GetWindowLongW.argtypes = [wt.HWND, ctypes.c_int]
        u.GetWindowThreadProcessId.argtypes = [wt.HWND,
                                               ctypes.POINTER(wt.DWORD)]
        u.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
        u.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        u.GetForegroundWindow.restype = wt.HWND
        _u32["u"] = u
    return _u32["u"]


def base_name(proc):
    p = (proc or "").lower()
    return p[:-4] if p.endswith(".exe") else p


def friendly_app_name(proc, title):
    base = base_name(proc)
    if base in APP_NICE_NAMES:
        return APP_NICE_NAMES[base]
    if base in ("applicationframehost", ""):
        return title or "that window"
    return base.replace("_", " ").title()


def top_windows():
    """Visible app windows, front-most first: [(hwnd, pid, process, title)]."""
    import ctypes.wintypes as wt
    import psutil
    u = user32_api()
    found = []
    skip_classes = {"Progman", "WorkerW", "Shell_TrayWnd",
                    "Shell_SecondaryTrayWnd"}

    def visit(hwnd, _):
        try:
            if not u.IsWindowVisible(hwnd):
                return True
            length = u.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            if u.GetWindowLongW(hwnd, -20) & 0x80:     # tool window
                return True
            cloaked = ctypes.c_int(0)                   # hidden UWP windows
            ctypes.windll.dwmapi.DwmGetWindowAttribute(
                wt.HWND(hwnd), 14, ctypes.byref(cloaked), 4)
            if cloaked.value:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            u.GetWindowTextW(hwnd, title, length + 1)
            klass = ctypes.create_unicode_buffer(256)
            u.GetClassNameW(hwnd, klass, 256)
            if klass.value in skip_classes:
                return True
            pid = wt.DWORD(0)
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                proc = psutil.Process(pid.value).name()
            except Exception:
                proc = ""
            found.append((hwnd, pid.value, proc, title.value))
        except Exception:
            pass
        return True

    callback = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(visit)
    u.EnumWindows(callback, 0)
    return found


def front_window():
    """The window the user is working in (never Optimus itself)."""
    me = os.getpid()
    wins = [w for w in top_windows() if w[1] != me]
    if not wins:
        return None
    front = user32_api().GetForegroundWindow()
    for w in wins:
        if w[0] == front:
            return w
    return wins[0]


def pick_windows(words):
    """Which windows does the user mean? -> (windows, spoken name)."""
    me = os.getpid()
    wins = [w for w in top_windows() if w[1] != me]
    name_words = [w for w in words if w not in WINDOW_FILLER]
    if not name_words:                      # "the current window"
        front = front_window()
        if not front:
            return [], ""
        return [front], friendly_app_name(front[2], front[3])
    key = norm("".join(name_words))
    hits = [w for w in wins if key in norm(base_name(w[2]))
            or key in norm(w[3])]
    if not hits:
        by_app = {}
        for w in wins:
            by_app.setdefault(norm(base_name(w[2])), []).append(w)
        close = difflib.get_close_matches(key, list(by_app), n=1, cutoff=0.7)
        if close:
            hits = by_app[close[0]]
    if not hits:
        return [], " ".join(name_words)
    return hits, friendly_app_name(hits[0][2], hits[0][3])


def minimize_command(words):
    u = user32_api()
    if set(words) & {"all", "everything"}:
        for vk, flags in ((0x5B, 0), (0x44, 0), (0x44, 2), (0x5B, 2)):
            ctypes.windll.user32.keybd_event(vk, 0, flags, 0)   # Win + D
        return "Minimized everything."
    windows, name = pick_windows(words)
    if not windows:
        return ("I can't find %s open." % name) if name else \
            "I can't see a window to minimize."
    for w in windows:
        u.ShowWindow(w[0], 6)                                   # SW_MINIMIZE
    time.sleep(0.4)
    if not any(u.IsIconic(w[0]) for w in windows):
        return "I couldn't minimize %s." % name
    return "Minimized %s." % name


def close_window_command(words, force=False):
    u = user32_api()
    windows, name = pick_windows(words)
    if not windows:
        return ("I can't find %s open." % name) if name else \
            "I can't see a window to close."
    blocked = PROTECTED if force else (PROTECTED - {"explorer"})
    windows = [w for w in windows if base_name(w[2]) not in blocked]
    if not windows:
        return "I can't close that one, %s." % USER_NAME
    if force:
        for pid in sorted({w[1] for w in windows}):
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                           capture_output=True, creationflags=0x08000000)
        time.sleep(0.7)
        if any(u.IsWindow(w[0]) for w in windows):
            return "I couldn't force %s to close." % name
        return "Force closed %s." % name
    for w in windows:
        u.PostMessageW(w[0], 0x0010, 0, 0)                      # WM_CLOSE
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if not any(u.IsWindow(w[0]) and u.IsWindowVisible(w[0])
                   for w in windows):
            break
        time.sleep(0.15)
    if any(u.IsWindow(w[0]) and u.IsWindowVisible(w[0]) for w in windows):
        return ("%s didn't close. It's probably asking whether to save "
                "something, so take a look. Or say force close %s and I'll "
                "shut it down." % (name, name.lower()))
    time.sleep(0.8)
    import psutil
    stays = [w for w in windows
             if base_name(w[2]) not in ("explorer", "applicationframehost")
             and psutil.pid_exists(w[1])]
    if stays:
        return ("Closed the %s window, but it's still running in the "
                "background. Say force close %s to shut it down completely."
                % (name, name.lower()))
    return "Closed %s." % name


# ======================== laptop powers ========================
def press_key(vk, times=1):
    try:
        for _ in range(times):
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            time.sleep(0.01)
    except Exception as error:
        print("Key press failed:", error)


def volume_control(t, words):
    numbers = re.findall(r"\d+", t)
    if "mute" in words or "unmute" in words:
        press_key(VK["mute"])
        return "Toggling mute."
    if numbers:
        pct = max(0, min(100, int(numbers[0])))
        press_key(VK["down"], 50)
        if pct:
            press_key(VK["up"], pct // 2)
        return "Volume set to %d percent." % pct
    if any(w in words for w in ("max", "maximum", "full")):
        press_key(VK["up"], 50)
        return "Volume at maximum."
    if any(w in words for w in ("up", "increase", "raise", "louder",
                                "higher")):
        press_key(VK["up"], 5)
        return "Turning it up."
    if any(w in words for w in ("down", "decrease", "lower", "quieter",
                                "reduce")):
        press_key(VK["down"], 5)
        return "Turning it down."
    return None


def get_brightness():
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance -Namespace root/WMI -ClassName "
             "WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True, text=True)
        return int(result.stdout.strip().splitlines()[0])
    except Exception:
        return None


def set_brightness(pct):
    pct = max(0, min(100, pct))
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance -Namespace root/WMI -ClassName "
         "WmiMonitorBrightnessMethods | Invoke-CimMethod -MethodName "
         "WmiSetBrightness -Arguments @{Timeout=1; Brightness=%d} "
         "| Out-Null" % pct], capture_output=True)
    return pct


def brightness_command(t, words):
    numbers = re.findall(r"\d+", t)
    if numbers:
        return "Brightness set to %d percent." % set_brightness(
            int(numbers[0]))
    current = get_brightness()
    if current is None:
        return "I can't control the brightness on this display."
    if any(w in words for w in ("up", "increase", "raise", "brighter",
                                "higher")):
        return "Brightness at %d percent." % set_brightness(current + 20)
    if any(w in words for w in ("down", "decrease", "lower", "dim",
                                "darker", "reduce")):
        return "Brightness at %d percent." % set_brightness(current - 20)
    return "Brightness is at %d percent." % current


def media_command(t, words):
    verb, rest = words[0], words[1:]
    only_nouns = all(w in MEDIA_NOUNS for w in rest)
    has_song = any(w in words for w in ("song", "track", "music"))
    if verb in ("pause", "resume") and only_nouns:
        press_key(VK["playpause"])
        return "Done."
    if verb == "play" and only_nouns:
        press_key(VK["playpause"])
        return "Done."
    if ((verb in ("next", "skip") and only_nouns)
            or (("next" in words or "skip" in words) and has_song)):
        press_key(VK["next"])
        return "Skipping to the next track."
    if ((verb in ("previous", "rewind") and only_nouns)
            or ("previous" in words and has_song)):
        press_key(VK["prev"])
        return "Going back to the previous track."
    if verb == "stop" and rest and only_nouns:
        press_key(VK["stop"])
        return "Stopped."
    if verb == "play" and rest:
        return play_query(" ".join(rest))
    if "brightness" in words and len(words) <= 7:
        return brightness_command(t, words)
    if len(words) <= 7 and any(w in words for w in (
            "volume", "mute", "unmute", "louder", "quieter")):
        return volume_control(t, words)
    return None


def play_query(query):
    query = re.sub(r"\s+(on|in|using)\s+(youtube|spotify)$", "", query)
    use_spotify = "spotify" in query
    query = query.replace("spotify", "").strip()
    if not query:
        return "What should I play?"
    if use_spotify:
        os.startfile("spotify:search:" + urllib.parse.quote(query))
        return "Searching Spotify for " + query + "."
    try:
        html = http_get("https://www.youtube.com/results?search_query="
                        + urllib.parse.quote_plus(query))
        match = re.search(r'"videoId":"([\w-]{11})"', html)
        if match:
            webbrowser.open("https://www.youtube.com/watch?v="
                            + match.group(1))
            return "Playing " + query + " on YouTube."
    except Exception as error:
        print("YouTube lookup failed:", error)
    webbrowser.open("https://www.youtube.com/results?search_query="
                    + urllib.parse.quote_plus(query))
    return "Here are the YouTube results for " + query + "."


def battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        return "I can't read a battery on this machine."
    status = "and charging" if battery.power_plugged else "and not charging"
    return "Battery is at %d percent, %s." % (battery.percent, status)


def system_status():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    text = "Processor is at %d percent and memory is at %d percent." % (
        cpu, ram)
    battery = psutil.sensors_battery()
    if battery is not None:
        text += " Battery is at %d percent." % battery.percent
    return text


# ======================== timers and reminders ========================
def save_alarms():
    with alarm_lock:
        try:
            with open(ALARMS_FILE, "w", encoding="utf-8") as f:
                json.dump(alarms, f)
        except Exception:
            pass


def load_alarms():
    try:
        with open(ALARMS_FILE, encoding="utf-8") as f:
            alarms.extend(json.load(f))
    except Exception:
        pass


def add_alarm(due, kind, spoken, label):
    with alarm_lock:
        alarms.append({"due": due, "kind": kind, "say": spoken,
                       "label": label})
    save_alarms()


def scheduler_loop():
    while True:
        time.sleep(1)
        now = time.time()
        fired = []
        with alarm_lock:
            for a in list(alarms):
                if a["due"] <= now:
                    fired.append(a)
                    alarms.remove(a)
        if fired:
            save_alarms()
            for a in fired:
                announce_queue.put(a["say"])


def process_announcements():
    spoke = False
    while True:
        try:
            message = announce_queue.get_nowait()
        except queue.Empty:
            break
        try:
            import winsound
            winsound.Beep(880, 180)
            winsound.Beep(1175, 250)
        except Exception:
            pass
        say(message)
        spoke = True
    if spoke:
        wait_speech()


def describe_alarms(kind=None):
    with alarm_lock:
        items = [a for a in alarms if kind is None or a["kind"] == kind]
    if not items:
        noun = {"timer": "timers", "reminder": "reminders"}.get(
            kind, "timers or reminders")
        return "You have no active %s." % noun
    parts = []
    for a in sorted(items, key=lambda x: x["due"]):
        if a["kind"] == "timer":
            parts.append("a timer with %s left"
                         % format_duration(a["due"] - time.time()))
        else:
            what = ("to " + a["label"] + " ") if a["label"] else ""
            parts.append("a reminder %sat %s" % (what, format_clock(a["due"])))
    return "You have " + ", and ".join(parts) + "."


def alarms_command(t):
    tt = numberize(t)
    words = tt.split()
    timer = "timer" in words or "timers" in words
    remind = (any(w in words for w in ("remind", "reminder", "reminders",
                                       "alarm", "alarms"))
              or ("wake" in words and "me" in words))
    if not (timer or remind):
        return None
    kind = "timer" if timer else "reminder"
    if any(w in words for w in ("cancel", "clear", "delete", "remove",
                                "stop")):
        with alarm_lock:
            before = len(alarms)
            alarms[:] = [a for a in alarms if a["kind"] != kind]
            removed = before - len(alarms)
        save_alarms()
        if not removed:
            return "There was nothing to cancel."
        return "All %s cleared." % ("timers" if timer else "reminders")
    duration = parse_duration(tt)
    clock = None if (duration or timer) else parse_clock(tt)
    if not duration and not clock:
        if any(w in words for w in ("what", "list", "show", "how", "any",
                                    "check", "left", "have")):
            return describe_alarms(kind)
        if timer:
            return "For how long, " + USER_NAME + "?"
        return ("Tell me when, for example: remind me to call mom in "
                "ten minutes.")
    if timer:
        add_alarm(time.time() + duration, "timer",
                  "Your %s timer is done, %s." % (format_duration(duration),
                                                  USER_NAME), "")
        return "Timer set for %s." % format_duration(duration)
    is_alarm = "alarm" in words or "alarms" in words or "wake" in words
    label = "" if is_alarm else reminder_label(tt)
    if duration:
        due = time.time() + duration
        when = "in " + format_duration(duration)
    else:
        due = clock
        when = "at " + format_clock(clock)
    if is_alarm:
        spoken = "Your alarm is going off, %s." % USER_NAME
    elif label:
        spoken = "Reminder, %s: %s." % (USER_NAME, label)
    else:
        spoken = "Reminder, %s. This is the reminder you asked for." % USER_NAME
    add_alarm(due, "reminder", spoken, label)
    if is_alarm:
        return "Alarm set %s." % when
    return "I'll remind you %s%s." % (("to " + label + " ") if label else "",
                                      when)


# ======================== screenshots ========================
def foreground_title():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""


def save_shots():
    try:
        with open(SHOTS_FILE, "w", encoding="utf-8") as f:
            json.dump(shots, f)
    except Exception:
        pass


def load_shots():
    try:
        with open(SHOTS_FILE, encoding="utf-8") as f:
            shots.extend(json.load(f))
    except Exception:
        pass


def ocr_entry(entry):
    """Optional: read the text inside a screenshot so it can be searched."""
    try:
        if _ocr["engine"] is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                _ocr["engine"] = RapidOCR()
            except Exception:
                _ocr["engine"] = False
        if not _ocr["engine"]:
            return
        result, _ = _ocr["engine"](entry["path"])
        entry["text"] = " ".join(r[1] for r in (result or []))
        save_shots()
    except Exception as error:
        print("Screenshot reading failed:", error)


def take_screenshot():
    from PIL import ImageGrab
    os.makedirs(SHOT_DIR, exist_ok=True)
    title = foreground_title()
    now = datetime.now()
    path = os.path.join(SHOT_DIR, now.strftime("screenshot_%Y-%m-%d_%H-%M-%S.png"))
    ImageGrab.grab(all_screens=True).save(path)
    entry = {"path": path, "time": now.timestamp(), "title": title,
             "text": ""}
    shots.append(entry)
    save_shots()
    threading.Thread(target=ocr_entry, args=(entry,), daemon=True).start()
    return path


def screenshot_files():
    files = []
    for folder in (SHOT_DIR, WIN_SHOT_DIR):
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                if name.lower().endswith((".png", ".jpg", ".jpeg")):
                    path = os.path.join(folder, name)
                    try:
                        files.append((os.path.getmtime(path), path))
                    except OSError:
                        pass
    return sorted(files, reverse=True)


SHOT_STOP = {"find", "search", "show", "open", "where", "look", "for", "of",
             "the", "a", "an", "with", "about", "that", "has", "have",
             "showing", "i", "took", "my", "screenshot", "screenshots",
             "from", "in", "on", "me", "latest", "last", "recent",
             "newest", "taken", "and", "it", "was", "is", "to"}


def search_screenshots(t, words):
    day = None
    today = datetime.now().date()
    if "today" in words:
        day = today
    elif "yesterday" in words:
        day = today - timedelta(days=1)
    terms = [w for w in words if w not in SHOT_STOP
             and w not in ("today", "yesterday")]
    best, best_score = None, 0
    for e in shots:
        haystack = (e.get("title", "") + " " + e.get("text", "")).lower()
        score = sum(1 for w in terms if w in haystack)
        if not terms:
            score = 0
        if day and datetime.fromtimestamp(e["time"]).date() == day:
            score += 1 if terms else 2
        if score > best_score and os.path.exists(e["path"]):
            best, best_score = e["path"], score
    if best:
        return best
    if day:
        for mtime, path in screenshot_files():
            if datetime.fromtimestamp(mtime).date() == day:
                return path
    return None


def screenshot_command(t, words):
    if "screenshot" not in words and "screenshots" not in words:
        if not ("screen" in words and any(
                w in words for w in ("capture", "grab", "snap"))):
            return None
    if "folder" in words:
        os.makedirs(SHOT_DIR, exist_ok=True)
        os.startfile(SHOT_DIR)
        return "Opening your screenshots folder."
    if any(w in words for w in ("take", "capture", "grab", "snap", "make")) \
            or words in (["screenshot"], ["screen", "capture"]):
        take_screenshot()
        return "Screenshot saved in your Pictures folder."
    if any(w in words for w in ("latest", "last", "recent", "newest")):
        files = screenshot_files()
        if not files:
            return "I can't find any screenshots yet."
        os.startfile(files[0][1])
        return "Opening your latest screenshot."
    path = search_screenshots(t, words)
    if path:
        os.startfile(path)
        return "Opening that screenshot."
    return ("I couldn't find a matching screenshot. I can search by the "
            "window name, the date, or the text inside it.")


# ======================== weather, news, web search ========================
def ip_location():
    providers = [
        ("https://ipwho.is/", "latitude", "longitude"),
        ("https://ipapi.co/json/", "latitude", "longitude"),
        ("http://ip-api.com/json/?fields=status,city,lat,lon", "lat", "lon"),
    ]
    for url, lat_key, lon_key in providers:
        try:
            data = json.loads(http_get(url, timeout=5))
            if (data.get(lat_key) is not None and data.get("success", True)
                    and data.get("status", "success") == "success"):
                return (data.get("city") or "your area", data[lat_key],
                        data[lon_key])
        except Exception as error:
            print("Location lookup failed:", url, error)
    return (None, None, None)


def get_location(city):
    key = (city or my_city() or "").strip().lower()
    if key in _loc_cache:
        return _loc_cache[key]
    if key:
        data = json.loads(http_get(
            "https://geocoding-api.open-meteo.com/v1/search?name=%s"
            "&count=1&language=en&format=json" % urllib.parse.quote(key)))
        res = (data.get("results") or [None])[0]
        loc = ((res["name"], res["latitude"], res["longitude"])
               if res else (None, None, None))
    else:
        loc = ip_location()
    if loc[1] is not None:
        _loc_cache[key] = loc
    return loc


def weather_fallback(name, lat, lon):
    place = ("%s,%s" % (lat, lon)) if lat is not None else \
        urllib.parse.quote(name)
    text = http_get("https://wttr.in/%s?format=%%C,+%%t,+feels+like+%%f"
                    % place, timeout=8).strip()
    if not text or "<" in text or "Unknown" in text:
        raise ValueError("bad reply from wttr.in")
    return "In %s it's %s." % (name, text.replace("+", ""))


def weather_report(city, tomorrow):
    try:
        name, lat, lon = get_location(city)
    except Exception as error:
        print("Location error:", error)
        return "I can't reach the internet right now, " + USER_NAME + "."
    if lat is None:
        if city or my_city():
            return "I couldn't find that place."
        return ("I couldn't work out where you are, %s. Say: my city is, "
                "and then the name of your city." % USER_NAME)
    try:
        data = json.loads(http_get(
            "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
            "&current=temperature_2m,apparent_temperature,weather_code"
            "&daily=temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,weather_code"
            "&timezone=auto&forecast_days=2" % (lat, lon)))
        cur, day = data["current"], data["daily"]
        i = 1 if tomorrow else 0
        high = round(day["temperature_2m_max"][i])
        low = round(day["temperature_2m_min"][i])
        rain = day["precipitation_probability_max"][i]
        rain_text = (" There is a %d percent chance of rain." % rain
                     if rain is not None and rain >= 20 else "")
        if tomorrow:
            sky = WEATHER_WORDS.get(day["weather_code"][1], "changeable")
            return ("Tomorrow in %s will be %s, with a high of %d and a low "
                    "of %d degrees.%s" % (name, sky, high, low, rain_text))
        sky = WEATHER_WORDS.get(cur["weather_code"], "changeable")
        return ("In %s it's %d degrees and %s, feeling like %d. Today's high "
                "is %d and the low is %d.%s"
                % (name, round(cur["temperature_2m"]), sky,
                   round(cur["apparent_temperature"]), high, low, rain_text))
    except Exception as error:
        print("Weather error:", error)
        try:
            return weather_fallback(name, lat, lon)
        except Exception as error2:
            print("Weather fallback error:", error2)
            return ("I can't reach the weather service right now, "
                    + USER_NAME + ".")


def weather_command(t, words):
    m = re.search(r"\b(?:in|at|for)\s+([a-z][a-z ]*?)"
                  r"(?:\s+(?:today|tomorrow|tonight|now|please))?\s*$", t)
    city = m.group(1).strip() if m else ""
    if city in ("today", "tomorrow", "tonight", "now") or \
            city.startswith("the "):
        city = ""
    return weather_report(city, "tomorrow" in words)


def fetch_headlines(url, count=5, with_source=False):
    root = ET.fromstring(http_get(url, timeout=10))
    out = []
    for item in root.iter("item"):
        raw = (item.findtext("title") or "").strip()
        title, _, source = raw.rpartition(" - ")
        if not title:
            title, source = raw, ""
        title = title.strip().rstrip(".")
        if title:
            out.append("%s (%s)" % (title, source)
                       if with_source and source else title)
        if len(out) >= count:
            break
    return out


def news_loop():
    while True:
        try:
            news_cache["titles"] = fetch_headlines(
                "https://news.google.com/rss?%s" % NEWS_REGION, 6)
        except Exception as error:
            print("News refresh failed:", error)
        time.sleep(1800)


def news_report(words):
    try:
        topic = next((NEWS_TOPICS[w] for w in words if w in NEWS_TOPICS),
                     None)
        if topic:
            url = ("https://news.google.com/rss/headlines/section/topic/%s?%s"
                   % (topic, NEWS_REGION))
        else:
            url = "https://news.google.com/rss?%s" % NEWS_REGION
        titles = fetch_headlines(url, 5)
        if not titles:
            return "I couldn't find any headlines."
        ordinals = ["First", "Second", "Third", "Fourth", "Fifth"]
        return (["Here are the top headlines, " + USER_NAME + "."]
                + ["%s, %s." % (ordinals[i], t) for i, t in enumerate(titles)])
    except Exception as error:
        print("News error:", error)
        return "I can't reach the news service right now, " + USER_NAME + "."


def research_query(t):
    for pattern in RESEARCH_RES:
        m = re.match(pattern, t)
        if m:
            return m.group(1).strip()
    return None


def search_news(query):
    url = "https://news.google.com/rss/search?q=%s&%s" % (
        urllib.parse.quote_plus(query), NEWS_REGION)
    return fetch_headlines(url, 5, with_source=True)


def wiki_summary(query):
    found = json.loads(http_get(
        "https://en.wikipedia.org/w/rest.php/v1/search/page?q=%s&limit=1"
        % urllib.parse.quote(query)))
    pages = found.get("pages") or []
    if not pages:
        return ""
    summary = json.loads(http_get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/%s"
        % urllib.parse.quote(pages[0]["key"], safe="")))
    return first_sentences(summary.get("extract", ""), 3, 500)


def ddg_results(query):
    page = http_get("https://html.duckduckgo.com/html/?q="
                    + urllib.parse.quote_plus(query), timeout=8)
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', page, re.S)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page,
                          re.S)
    out = []
    for title, snippet in zip(titles, snippets):
        t = html_lib.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        sn = html_lib.unescape(re.sub(r"<[^>]+>", "", snippet)).strip()
        out.append("%s: %s" % (t, sn[:220]))
        if len(out) >= 3:
            break
    return out


def gather_sources(query):
    """Collect fresh facts from news, an encyclopedia and the web."""
    found = {}

    def run(name, fn):
        try:
            found[name] = fn(query)
        except Exception as error:
            print("%s lookup failed: %s" % (name, error))

    jobs = [("news", search_news), ("wiki", wiki_summary),
            ("web", ddg_results)]
    threads = [threading.Thread(target=run, args=job, daemon=True)
               for job in jobs]
    for th in threads:
        th.start()
    deadline = time.time() + 12
    for th in threads:
        th.join(max(0.1, deadline - time.time()))
    parts = []
    if found.get("news"):
        parts.append("Recent news: " + " | ".join(found["news"]) + ".")
    if found.get("wiki"):
        parts.append("Encyclopedia: " + found["wiki"])
    if found.get("web"):
        parts.append("Web results: " + " | ".join(found["web"]))
    return " ".join(parts)[:2400]


GOOGLE_HINTS = {"best", "price", "prices", "buy", "cheap", "near", "review",
                "reviews", "vs", "versus", "deal", "deals", "download",
                "tutorial"}


def web_search(query):
    query = query.strip()
    if not query:
        return "What should I search for?"
    results_url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(
        query)
    if any(w in GOOGLE_HINTS for w in query.split()):
        webbrowser.open(results_url)
        return "Here are the search results for " + query + "."
    try:
        found = json.loads(http_get(
            "https://en.wikipedia.org/w/rest.php/v1/search/page?q=%s&limit=1"
            % urllib.parse.quote(query)))
        pages = found.get("pages") or []
        if pages:
            summary = json.loads(http_get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/%s"
                % urllib.parse.quote(pages[0]["key"], safe="")))
            extract = summary.get("extract", "")
            if extract:
                return first_sentences(extract)
    except Exception as error:
        print("Search error:", error)
    webbrowser.open(results_url)
    return "I've opened the search results for you."


# ======================== voice lock (only your voice) ========================
def load_speaker():
    try:
        import sherpa_onnx
        if not os.path.exists(SPEAKER_MODEL_PATH):
            print("Voice lock model not found, so the voice lock is off.")
            return
        config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=SPEAKER_MODEL_PATH, num_threads=2, debug=False,
            provider="cpu")
        speaker["extractor"] = sherpa_onnx.SpeakerEmbeddingExtractor(config)
        if os.path.exists(VOICEPRINT_FILE):
            speaker["print"] = np.load(VOICEPRINT_FILE)
        print("Voice lock ready" + (
            "" if speaker["print"] is not None
            else " (not trained yet - say: learn my voice)"))
    except Exception as error:
        print("Voice lock unavailable:", error)


def lock_enabled():
    return bool(settings.get("voice_lock", VOICE_LOCK))


def voice_lock_active():
    return (lock_enabled() and speaker["extractor"] is not None
            and speaker["print"] is not None)


def embed(audio):
    extractor = speaker["extractor"]
    stream = extractor.create_stream()
    stream.accept_waveform(sample_rate=SAMPLE_RATE,
                           waveform=np.asarray(audio, dtype=np.float32))
    stream.input_finished()
    vec = np.asarray(extractor.compute(stream), dtype=np.float32)
    return vec / (np.linalg.norm(vec) + 1e-9)


def speaker_ok(audio, strict=False):
    """True if this sounds like the enrolled owner (or the lock is off)."""
    if not voice_lock_active():
        return True
    try:
        score = float(np.dot(embed(audio), speaker["print"]))
    except Exception as error:
        print("Voice check failed:", error)
        return not strict
    need = float(settings.get("lock_threshold", VOICE_LOCK_THRESHOLD))
    if not strict and len(audio) < SAMPLE_RATE:
        need -= 0.08
    ok = score >= need
    print("Voice match: %.2f (needs %.2f) -> %s"
          % (score, need, "ok" if ok else "REJECTED"))
    if not ok:
        log_event("rejected voice", "score %.2f" % score)
    return ok


def enroll_voice():
    if speaker["extractor"] is None:
        say("The voice lock model isn't installed yet, %s." % USER_NAME)
        return
    say("Voice training. I'll say a sentence, and you repeat it after me. "
        "We'll do six.")
    wait_speech()
    vectors = []
    for number, sentence in enumerate(ENROLL_PROMPTS, 1):
        for attempt in range(2):
            say(sentence)
            wait_speech()
            set_orb("listening")
            audio = record_until_silence(max_seconds=10, wait_seconds=8)
            if audio is not None and len(audio) >= 1.0 * SAMPLE_RATE:
                vectors.append(embed(audio))
                break
            say("I didn't catch that. Once more.")
            wait_speech()
    if len(vectors) < 4:
        say("I couldn't get enough clear samples. Please try again in a "
            "quieter place.")
        return
    mean = np.mean(vectors, axis=0)
    mean = mean / (np.linalg.norm(mean) + 1e-9)
    np.save(VOICEPRINT_FILE, mean)
    speaker["print"] = mean
    scores = [float(np.dot(v, mean)) for v in vectors]
    average = sum(scores) / len(scores)
    threshold = round(max(0.35, min(0.5, average - 0.3)), 2)
    save_setting("lock_threshold", threshold)
    save_setting("voice_lock", True)
    print("Voice training scores:", [round(s, 2) for s in scores],
          "threshold set to", threshold)
    say("Done, %s. From now on I'll answer only to your voice." % USER_NAME)


def voice_lock_command(t, words):
    if "voice" not in words or "lock" not in words:
        return None
    if "off" in words or "disable" in words:
        save_setting("voice_lock", False)
        return "Voice lock off. I'll answer to anyone now."
    if "on" in words or "enable" in words:
        save_setting("voice_lock", True)
        if speaker["print"] is None:
            return ("Voice lock is on, but I haven't learned your voice yet. "
                    "Say: learn my voice.")
        return "Voice lock on. I'll answer only to you."
    if voice_lock_active():
        return "Voice lock is on and working."
    if speaker["extractor"] is None:
        return "The voice lock model isn't installed yet."
    if speaker["print"] is None:
        return "I haven't learned your voice yet. Say: learn my voice."
    return "Voice lock is off."


VOICE_VERBS = {"change", "switch", "use", "set", "make", "speak", "talk",
               "sound", "go", "put", "turn", "back", "become", "give",
               "choose", "pick", "select", "swap"}


def voice_style_command(t, words):
    if "voice" not in words or not (VOICE_VERBS & set(words)):
        return None
    for name, pack in VOICE_PACKS.items():
        if name in words and name not in ("jarvis", "friendly", "overlord"):
            save_setting("voice_style", name)
            return "Switching to the %s voice." % pack[4]
    if any(w in words for w in ("megatron", "overlord", "villain", "deep",
                                "menacing")):
        save_setting("voice_style", "overlord")
        return "As you command. The overlord voice is online."
    if any(w in words for w in ("jarvis", "butler", "british", "male",
                                "man")):
        save_setting("voice_style", "jarvis")
        return "Back to the butler voice, %s." % USER_NAME
    if any(w in words for w in ("friendly", "soft", "female", "woman",
                                "girl", "lady", "normal", "default")):
        save_setting("voice_style", "friendly")
        return "Hi! I'll use my friendly voice from now on."
    return None


# ======================== confirmations, code red, power ========================
YES_WORDS = {"yes", "execute", "confirm", "confirmed", "affirmative",
             "proceed", "sure"}
NO_WORDS = {"no", "abort", "cancel", "stop", "negative", "nope"}


def confirm(prompt_text, timeout=10):
    """Ask out loud, then wait for a spoken yes in the owner's voice."""
    say(prompt_text)
    wait_speech()
    set_orb("listening")
    audio = record_until_silence(max_seconds=6, silence_seconds=0.8,
                                 wait_seconds=timeout)
    if audio is None:
        return False
    if not speaker_ok(audio, strict=True):
        say("Voice not recognised. Standing down.")
        wait_speech()
        return False
    text, _ = transcribe(model, audio, prompt="yes execute, abort, confirm")
    heard = set(text.split())
    print("Confirmation heard:", text)
    return bool(heard & YES_WORDS) and not (heard & NO_WORDS)


def close_all_apps():
    procs = ps_json("Get-Process | Where-Object "
                    "{$_.MainWindowTitle -ne ''} | Select-Object "
                    "Id,ProcessName,MainWindowTitle | ConvertTo-Json")
    me = os.getpid()
    skip = PROTECTED | {"searchhost", "shellexperiencehost",
                        "startmenuexperiencehost", "textinputhost",
                        "lockapp", "widgets"}
    closed = 0
    for p in procs:
        if p["Id"] == me or p["ProcessName"].lower() in skip:
            continue
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process -Id %d).CloseMainWindow()" % p["Id"]],
                       capture_output=True)
        closed += 1
    return closed


def code_red():
    ok = confirm("Code red acknowledged. This will close every open "
                 "application and shut the system down. Are you absolutely "
                 "sure? Say yes, execute, to proceed, or abort to stand "
                 "down.", timeout=12)
    if not ok:
        say("Code red cancelled. Standing down.")
        return
    say("Confirmed. Closing all applications. System shutdown in thirty "
        "seconds. Say abort to cancel.")
    wait_speech()
    close_all_apps()
    subprocess.run(["shutdown", "/s", "/t", "30", "/c", "Optimus code red"],
                   capture_output=True)
    for _ in range(6):
        audio = record_until_silence(max_seconds=4, silence_seconds=0.7,
                                     wait_seconds=5)
        if audio is None or not speaker_ok(audio, strict=True):
            continue
        text, _ = transcribe(model, audio, prompt="abort, cancel")
        if set(text.split()) & {"abort", "cancel", "stop"}:
            subprocess.run(["shutdown", "/a"], capture_output=True)
            say("Shutdown aborted. Standing down.")
            return


def run_action(name):
    if name == "shutdown":
        subprocess.run(["shutdown", "/s", "/t", "20"], capture_output=True)
        say("Shutting down in twenty seconds. Right-click my tray icon and "
            "choose Abort shutdown to cancel.")
    elif name == "restart":
        subprocess.run(["shutdown", "/r", "/t", "20"], capture_output=True)
        say("Restarting in twenty seconds. Right-click my tray icon and "
            "choose Abort shutdown to cancel.")
    elif name == "sleep":
        say("Going to sleep. Good night, %s." % USER_NAME)
        wait_speech()
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState",
                          "0,1,0"])
    elif name == "recycle":
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Clear-RecycleBin -Force -ErrorAction "
                        "SilentlyContinue"], capture_output=True)
        say("Recycle bin emptied.")


PC_WORDS = ("laptop", "computer", "pc", "system", "windows", "machine")


def power_command(t, words):
    pc = any(w in words for w in PC_WORDS)
    if ("recycle" in words and "bin" in words
            and any(w in words for w in ("empty", "clear"))):
        return ("confirm", "recycle",
                "Permanently empty the recycle bin? Say yes, execute, to "
                "confirm.")
    if pc and (("shut" in words and "down" in words) or "shutdown" in words
               or ("power" in words and "off" in words)):
        return ("confirm", "shutdown",
                "Shut the computer down? Say yes, execute, to confirm.")
    if (pc or len(words) <= 3) and any(w in words for w in
                                       ("restart", "reboot")):
        return ("confirm", "restart",
                "Restart the computer? Say yes, execute, to confirm.")
    if pc and "sleep" in words:
        return ("confirm", "sleep",
                "Put the computer to sleep? Say yes, execute, to confirm.")
    return None


# ======================== memory, notes, to-do ========================
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def memory_text():
    items = load_json(MEMORY_FILE, [])
    return " | ".join(items)[-1200:]


def memory_command(t):
    m = re.match(r"^remember(?: that)?\s+(.+)$", t)
    if m:
        items = load_json(MEMORY_FILE, [])
        items.append(m.group(1).strip())
        save_json(MEMORY_FILE, items[-60:])
        return "Noted. I'll remember that."
    if any(p in t for p in ("what do you remember", "what do you know about me",
                            "what did i tell you")):
        items = load_json(MEMORY_FILE, [])
        if not items:
            return "You haven't asked me to remember anything yet."
        return ["Here's what I remember."] + [i + "." for i in items[-8:]]
    if t in ("forget everything", "clear your memory", "clear my memory",
             "wipe your memory"):
        save_json(MEMORY_FILE, [])
        return "Memory cleared."
    m = re.match(r"^forget(?: that| about)?\s+(.+)$", t)
    if m:
        key = re.sub(r"^(?:the|my|about)\s+", "", m.group(1).strip())
        items = load_json(MEMORY_FILE, [])
        keep = [i for i in items if key not in i.lower()]
        save_json(MEMORY_FILE, keep)
        return ("Forgotten." if len(keep) < len(items)
                else "I didn't have anything about that.")
    return None


def notes_command(t):
    m = re.match(r"^(?:take a note|make a note|note down|write down)"
                 r"(?: that)?\s+(.+)$", t)
    if m:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (datetime.now().strftime("%d %b %H:%M"),
                                   m.group(1).strip()))
        return "Noted."
    if t in ("read my notes", "read notes", "show my notes", "what are my notes"):
        try:
            with open(NOTES_FILE, encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
        except Exception:
            lines = []
        if not lines:
            return "You have no notes yet."
        return ["Your latest notes."] + [re.sub(r"^\[[^\]]*\]\s*", "", ln)
                                         + "." for ln in lines[-5:]]
    if t in ("open my notes", "open notes"):
        if os.path.exists(NOTES_FILE):
            os.startfile(NOTES_FILE)
            return "Opening your notes."
        return "You have no notes yet."
    if t in ("clear my notes", "delete my notes"):
        try:
            os.remove(NOTES_FILE)
        except Exception:
            pass
        return "Notes cleared."
    return None


LIST_WORDS = r"(?:my |the )?(?:to do |todo |shopping |task )?list"


def todo_command(t):
    items = load_json(TODO_FILE, [])
    m = (re.match(r"^add\s+(.+?)\s+(?:to|on)\s+" + LIST_WORDS + "$", t)
         or re.match(r"^put\s+(.+?)\s+on\s+" + LIST_WORDS + "$", t))
    if m:
        items.append(m.group(1).strip())
        save_json(TODO_FILE, items)
        return "Added. You now have %d item%s on your list." % (
            len(items), "" if len(items) == 1 else "s")
    if any(p in t for p in ("what s on my list", "what is on my list",
                            "read my list", "show my list",
                            "my to do list", "my todo list")):
        if not items:
            return "Your list is empty."
        return ["You have %d item%s." % (len(items),
                                        "" if len(items) == 1 else "s")] \
            + [i + "." for i in items[:10]]
    if t in ("clear my list", "clear my to do list", "empty my list"):
        save_json(TODO_FILE, [])
        return "List cleared."
    m = (re.match(r"^(?:remove|delete)\s+(.+?)\s+from\s+" + LIST_WORDS + "$", t)
         or re.match(r"^(?:i finished|i completed|mark|tick off|cross off)\s+"
                     r"(.+?)(?:\s+as done|\s+done)?$", t))
    if m and items:
        key = m.group(1).strip()
        keep = [i for i in items if key not in i.lower()]
        if len(keep) < len(items):
            save_json(TODO_FILE, keep)
            return "Done. Removed it from your list."
        return "I couldn't find that on your list."
    return None


# ======================== modes, quiz, focus, gaming ========================
def mode_command(t, words):
    if "sarcasm" in words:
        if any(w in words for w in ("high", "max", "more", "up")):
            save_setting("mode", "sarcastic")
            return "Sarcasm turned up. Try to keep up."
        if any(w in words for w in ("low", "off", "less", "zero", "down")):
            save_setting("mode", "friendly")
            return "Sarcasm off. I'll be nice."
        save_setting("mode", "normal")
        return "Sarcasm back to normal."
    if "mode" in words:
        for name in MODES:
            if name in words:
                save_setting("mode", name)
                return "%s mode on." % name.title()
    m = re.match(r"^(?:quiz me|test me|give me a quiz)(?: on| about)?\s*(.*)$",
                 t)
    if m:
        quiz["topic"] = m.group(1).strip() or "general knowledge"
        return ("ask", "Start the quiz now with your first question.", "",
                "none")
    if t in ("stop quiz", "end quiz", "stop the quiz", "quiz over"):
        quiz["topic"] = None
        return "Quiz ended. Nicely done."
    return None


def focus_command(t, words):
    focus = ("focus" in words or "pomodoro" in words
             or ("study" in words and "session" in words))
    if not focus:
        return None
    if any(w in words for w in ("stop", "end", "cancel")):
        with alarm_lock:
            had = any(a["kind"] == "focus" for a in alarms)
            alarms[:] = [a for a in alarms if a["kind"] != "focus"]
        save_alarms()
        return "Focus mode ended." if had else "Focus mode wasn't running."
    minutes = FOCUS_MINUTES
    seconds = parse_duration(numberize(t))
    if seconds:
        minutes = max(1, seconds // 60)
    closed = 0
    for app in DISTRACTION_APPS:
        if close_app([app]).startswith("Closing"):
            closed += 1
    now = time.time()
    add_alarm(now + minutes * 60, "focus",
              "Focus session complete, %s. Take a %d minute break."
              % (USER_NAME, BREAK_MINUTES), "")
    add_alarm(now + (minutes + BREAK_MINUTES) * 60, "focus",
              "Break's over, %s. Ready for another round?" % USER_NAME, "")
    extra = (" I closed %d distracting apps." % closed) if closed else ""
    return "Focus mode on for %d minutes.%s" % (minutes, extra)


def gaming_command(t, words):
    if not ("gaming" in words or ("game" in words and "mode" in words)):
        return None
    if any(w in words for w in ("off", "stop", "end")):
        return "Game mode off. Hope you won."
    closed = sum(1 for a in GAMING_CLOSE_APPS
                 if close_app([a]).startswith("Closing"))
    try:
        set_brightness(100)
    except Exception:
        pass
    launched = open_target([GAMING_APP])
    return "Game mode on. I closed %d background apps. %s" % (closed, launched)


# ======================== browser, typing, keyboard ========================
BROWSER_TITLES = ("chrome", "edge", "firefox", "brave", "opera", "vivaldi")
KNOWN_SITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com",
    "gmail": "https://mail.google.com", "github": "https://github.com",
    "amazon": "https://www.amazon.in", "flipkart": "https://www.flipkart.com",
    "wikipedia": "https://www.wikipedia.org",
    "maps": "https://www.google.com/maps",
    "drive": "https://drive.google.com", "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com", "netflix": "https://www.netflix.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai",
}
SEARCH_SITES = {
    "youtube": "https://www.youtube.com/results?search_query=%s",
    "google": "https://www.google.com/search?q=%s",
    "amazon": "https://www.amazon.in/s?k=%s",
    "flipkart": "https://www.flipkart.com/search?q=%s",
    "wikipedia": "https://en.wikipedia.org/w/index.php?search=%s",
    "maps": "https://www.google.com/maps/search/%s",
    "google maps": "https://www.google.com/maps/search/%s",
    "github": "https://github.com/search?q=%s",
    "reddit": "https://www.reddit.com/search/?q=%s",
    "linkedin": "https://www.linkedin.com/search/results/all/?keywords=%s",
}
BROWSER_ACTIONS = [
    (("new tab", "open new tab"), ("ctrl", "t")),
    (("close tab", "close this tab"), ("ctrl", "w")),
    (("next tab",), ("ctrl", "tab")),
    (("previous tab", "last tab"), ("ctrl", "shift", "tab")),
    (("reopen tab", "reopen closed tab"), ("ctrl", "shift", "t")),
    (("go back", "back page", "previous page"), ("alt", "left")),
    (("go forward", "forward page"), ("alt", "right")),
    (("refresh", "reload", "refresh page", "reload page"), ("f5",)),
    (("zoom in",), ("ctrl", "=")),
    (("zoom out",), ("ctrl", "-")),
    (("reset zoom",), ("ctrl", "0")),
    (("full screen", "fullscreen"), ("f11",)),
    (("incognito", "private window", "new incognito window"),
     ("ctrl", "shift", "n")),
    (("bookmark this", "bookmark this page", "add bookmark"), ("ctrl", "d")),
    (("new window",), ("ctrl", "n")),
    (("browser history", "open history"), ("ctrl", "h")),
    (("stop loading",), ("esc",)),
]
KEY_PRESSES = {"enter": "enter", "tab": "tab", "escape": "esc",
               "backspace": "backspace", "delete": "delete", "space": "space",
               "up": "up", "down": "down", "left": "left", "right": "right"}
EDIT_ACTIONS = {
    "select all": ("ctrl", "a"), "copy that": ("ctrl", "c"),
    "copy this": ("ctrl", "c"), "copy it": ("ctrl", "c"),
    "paste": ("ctrl", "v"), "paste it": ("ctrl", "v"),
    "cut that": ("ctrl", "x"), "undo": ("ctrl", "z"),
    "undo that": ("ctrl", "z"), "redo": ("ctrl", "y"),
    "save this": ("ctrl", "s"), "save it": ("ctrl", "s"),
}


def browser_focused():
    title = foreground_title().lower()
    return any(b in title for b in BROWSER_TITLES)


def get_pyautogui():
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05
        return pyautogui
    except Exception as error:
        print("pyautogui is not installed:", error)
        return None


def set_clipboard(text):
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Console]::InputEncoding=[Text.Encoding]::UTF8; "
         "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=text, text=True, encoding="utf-8", capture_output=True)


def get_clipboard():
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
         "Get-Clipboard -Raw"],
        capture_output=True, text=True, encoding="utf-8")
    return result.stdout or ""


def type_text(text):
    py = get_pyautogui()
    if py is None:
        return False
    set_clipboard(text)
    time.sleep(0.1)
    py.hotkey("ctrl", "v")
    return True


def site_url(name):
    name = name.strip().lower().replace(" dot ", ".").replace(" ", "")
    if name in KNOWN_SITES:
        return KNOWN_SITES[name]
    if "." in name:
        return name if name.startswith("http") else "https://" + name
    return "https://www." + name + ".com"


def handle_dictation(raw, text):
    if text in ("stop dictation", "end dictation", "finish dictation",
                "stop typing"):
        dictation["on"] = False
        say("Dictation off.")
        wait_speech()
        return
    py = get_pyautogui()
    if text in ("new line", "next line", "press enter") and py:
        py.press("enter")
        return
    if text == "new paragraph" and py:
        py.press("enter")
        py.press("enter")
        return
    if raw.strip():
        type_text(raw.strip() + " ")


def browser_command(t, words):
    m = re.match(r"^(?:go to|visit|navigate to|browse to|open (?:the )?"
                 r"(?:website|site|web page|webpage))\s+(.+)$", t)
    if m:
        webbrowser.open(site_url(m.group(1)))
        return "Opening " + m.group(1).strip().replace(" dot ", ".") + "."
    m = re.match(r"^(?:search|find|look for)\s+(.+?)\s+(?:on|in)\s+"
                 r"(youtube|google maps|google|amazon|flipkart|wikipedia|maps|"
                 r"github|reddit|linkedin)$", t)
    if m:
        query, site = m.group(1).strip(), m.group(2)
        webbrowser.open(SEARCH_SITES[site] % urllib.parse.quote_plus(query))
        return "Searching %s for %s." % (site, query)
    m = re.match(r"^type\s+(.+)$", t)
    if m:
        text = m.group(1).strip()
        if type_text(text[:1].upper() + text[1:]):
            return "Typed."
        return "I need the pyautogui package to type for you."
    if t in EDIT_ACTIONS or t in ("scroll down", "scroll up",
                                  "scroll to the top", "scroll to the bottom",
                                  "page down", "page up"):
        py = get_pyautogui()
        if py is None:
            return "I need the pyautogui package for that."
        if t in EDIT_ACTIONS:
            py.hotkey(*EDIT_ACTIONS[t])
        elif t in ("scroll down", "page down"):
            py.scroll(-700)
        elif t in ("scroll up", "page up"):
            py.scroll(700)
        elif t == "scroll to the top":
            py.press("home")
        else:
            py.press("end")
        return "Done."
    m = re.match(r"^(?:press|hit|push)\s+(enter|tab|escape|backspace|delete|"
                 r"space|up|down|left|right)$", t)
    if m:
        py = get_pyautogui()
        if py is None:
            return "I need the pyautogui package for that."
        py.press(KEY_PRESSES[m.group(1)])
        return "Done."
    action = None
    m = re.match(r"^find\s+(.+?)\s+on (?:this |the )?page$", t)
    if m:
        action = ("find", m.group(1).strip())
    else:
        for phrases, keys in BROWSER_ACTIONS:
            if t in phrases:
                action = ("keys", keys)
                break
    if action is None:
        return None
    if not browser_focused():
        return "Please click on your browser first, %s." % USER_NAME
    py = get_pyautogui()
    if py is None:
        return "I need the pyautogui package for that."
    if action[0] == "find":
        py.hotkey("ctrl", "f")
        time.sleep(0.2)
        set_clipboard(action[1])
        py.hotkey("ctrl", "v")
        py.press("enter")
        return "Searching the page for " + action[1] + "."
    py.hotkey(*action[1])
    return "Done."


# ======================== screen questions and summaries ========================
SCREEN_EXACT = {"explain this", "read this", "look at this", "what is this",
                "what does this say", "what does this mean",
                "help me with this", "what is this error",
                "what do you see", "what can you see", "tell me what you see",
                "what am i looking at", "what is happening here",
                "what s happening here", "what s this", "what is on screen"}


def screen_question(t, words):
    if t in SCREEN_EXACT:
        return t
    if ("screen" in words and "screenshot" not in words
            and len(words) <= 12
            and any(w in words for w in ("what", "look", "read", "describe",
                                         "explain", "see", "summarize",
                                         "summarise", "tell", "help", "check",
                                         "analyze", "analyse", "review",
                                         "scan"))):
        return t
    if "looking" in words and "at" in words and len(words) <= 6:
        return t
    return None


def strip_html(page):
    page = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return " ".join(html_lib.unescape(page).split())


def read_file_text(path, limit=6000):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = "\n".join((p.extract_text() or "") for p in reader.pages[:12])
    elif ext == ".docx":
        import zipfile
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ",
                                        xml.replace("</w:p>", "\n")))
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read(limit * 2)
    return " ".join(text.split())[:limit]


def summarize_command(t, words):
    m = re.match(r"^(?:summarize|summarise|sum up)\s+(?:the |my |this )?(.+)$",
                 t)
    if not m:
        return None
    target = m.group(1).strip()
    ask = "Summarize this clearly in a few short sentences."
    try:
        if target in ("clipboard", "what i copied", "copied text", "copied"):
            text = get_clipboard().strip()
            if not text:
                return "Your clipboard is empty."
            return ("ask", ask, text[:5000], "doc")
        if target in ("page", "web page", "webpage", "article", "website",
                      "tab", "this page", "this article"):
            if not browser_focused():
                return "Please click on your browser first, %s." % USER_NAME
            py = get_pyautogui()
            if py is None:
                return "I need the pyautogui package for that."
            py.hotkey("ctrl", "l")
            time.sleep(0.2)
            py.hotkey("ctrl", "c")
            time.sleep(0.2)
            py.press("esc")
            url = get_clipboard().strip()
            if not url.startswith("http"):
                return "I couldn't read the page address."
            text = strip_html(http_get(url, timeout=12))
            if len(text) < 200:
                return "That page didn't give me enough text to read."
            return ("ask", ask, text[:5000], "doc")
        if "screen" in target:
            return ("screen", "Summarize what is on my screen.")
        name = " ".join(w for w in target.split() if w not in (
            "file", "pdf", "document", "doc", "called", "named"))
        path = find_best(name, FILES)
        if not path:
            return "I couldn't find a file called " + name + "."
        text = read_file_text(path)
        if not text:
            return "I couldn't read any text from that file."
        return ("ask", ask, text, "doc")
    except Exception as error:
        print("Summary error:", error)
        return "I couldn't read that, %s." % USER_NAME


# ======================== briefing and system settings ========================
def briefing_lines():
    now = datetime.now()
    lines = ["Here's your briefing, %s. It's %s."
             % (USER_NAME, now.strftime("%A, %d %B"))]
    weather = weather_report("", False)
    if weather and not weather.startswith(("I can't", "I couldn't")):
        lines.append(weather)
    reminders = describe_alarms()
    if not reminders.startswith("You have no"):
        lines.append(reminders)
    todos = load_json(TODO_FILE, [])
    if todos:
        lines.append("You have %d thing%s on your list, starting with %s."
                     % (len(todos), "" if len(todos) == 1 else "s", todos[0]))
    titles = list(news_cache["titles"])
    if not titles:
        try:
            titles = fetch_headlines(
                "https://news.google.com/rss?%s" % NEWS_REGION, 4)
        except Exception:
            titles = []
    if titles:
        lines.append("In the news. " + ". ".join(titles[:3]) + ".")
    lines.append("That's everything for now. Have a great day.")
    save_setting("last_briefing", now.strftime("%Y-%m-%d"))
    return lines


def set_theme(light):
    value = "1" if light else "0"
    for name in ("AppsUseLightTheme", "SystemUsesLightTheme"):
        subprocess.run(
            ["reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion"
             r"\Themes\Personalize", "/v", name, "/t", "REG_DWORD",
             "/d", value, "/f"], capture_output=True)


SETTINGS_PANELS = {
    "wifi": "ms-settings:network-wifi", "bluetooth": "ms-settings:bluetooth",
    "airplane": "ms-settings:network-airplanemode",
    "display": "ms-settings:display", "sound": "ms-settings:sound",
}


def system_command(t, words):
    if "dark" in words and ("mode" in words or "theme" in words):
        set_theme(False)
        return "Dark mode on."
    if "light" in words and ("mode" in words or "theme" in words):
        set_theme(True)
        return "Light mode on."
    for name, uri in SETTINGS_PANELS.items():
        if name in words and any(w in words for w in (
                "turn", "switch", "connect", "disconnect", "settings",
                "toggle", "enable", "disable", "on", "off")):
            os.startfile(uri)
            return ("I can't flip that switch without admin rights, so I've "
                    "opened its settings for you.")
    return None


# ======================== phone control (Telegram) ========================
def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def tg_api(token, method, params=None, timeout=10):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return json.loads(http_get(url, timeout=timeout))


def tg_send(token, chat_id, text):
    try:
        tg_api(token, "sendMessage", {"chat_id": chat_id, "text": text[:3500]})
    except Exception as error:
        print("Telegram send failed:", error)


def screenshot_jpeg_path():
    from PIL import ImageGrab
    img = ImageGrab.grab(all_screens=True).convert("RGB")
    if img.width > 1920:
        img = img.resize((1920, int(img.height * 1920 / img.width)))
    path = os.path.join(BASE_DIR, "remote_shot.jpg")
    img.save(path, "JPEG", quality=80)
    return path


def tg_send_photo(token, chat_id, path):
    boundary = "----optimus%d" % int(time.time())
    with open(path, "rb") as f:
        data = f.read()
    body = (("--%s\r\nContent-Disposition: form-data; name=\"chat_id\""
             "\r\n\r\n%s\r\n" % (boundary, chat_id)).encode("utf-8")
            + ("--%s\r\nContent-Disposition: form-data; name=\"photo\"; "
               "filename=\"screen.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n"
               % boundary).encode("utf-8")
            + data + ("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    request = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendPhoto" % token, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    urllib.request.urlopen(request, timeout=40).read()


def tg_handle(token, message):
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None or not text:
        return
    owner = settings.get("tg_owner")
    if owner is None:
        secret = read_text(TELEGRAM_SECRET_FILE)
        parts = text.split(None, 1)
        if (secret and len(parts) == 2 and parts[0] == "/pair"
                and parts[1].strip() == secret):
            save_setting("tg_owner", chat_id)
            tg_send(token, chat_id, "Paired. Send /help to see what I can do.")
        return
    if chat_id != owner:
        return
    cmd, _, arg = text.partition(" ")
    cmd = cmd.lower().split("@")[0]
    if cmd in ("/help", "/start"):
        tg_send(token, chat_id, "/battery /status /screenshot /lock /say "
                "<text> /shutdown (then /confirm) /cancel")
    elif cmd == "/battery":
        tg_send(token, chat_id, battery_status())
    elif cmd == "/status":
        tg_send(token, chat_id, system_status())
    elif cmd == "/lock":
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        tg_send(token, chat_id, "Locked.")
    elif cmd == "/screenshot":
        try:
            tg_send_photo(token, chat_id, screenshot_jpeg_path())
        except Exception as error:
            print("Telegram screenshot failed:", error)
            tg_send(token, chat_id, "I couldn't send the screenshot.")
    elif cmd == "/say" and arg.strip():
        say(arg.strip())
        tg_send(token, chat_id, "Said it.")
    elif cmd == "/shutdown":
        pending_remote["until"] = time.time() + 30
        tg_send(token, chat_id, "Send /confirm within 30 seconds to shut "
                "down the laptop.")
    elif cmd == "/confirm":
        if time.time() < pending_remote["until"]:
            pending_remote["until"] = 0
            subprocess.run(["shutdown", "/s", "/t", "30"], capture_output=True)
            tg_send(token, chat_id, "Shutting down in 30 seconds. Send "
                    "/cancel to stop it.")
        else:
            tg_send(token, chat_id, "Nothing to confirm.")
    elif cmd == "/cancel":
        pending_remote["until"] = 0
        subprocess.run(["shutdown", "/a"], capture_output=True)
        tg_send(token, chat_id, "Cancelled.")


def telegram_loop():
    token = read_text(TELEGRAM_TOKEN_FILE)
    if not token:
        return
    print("Telegram control is on")
    offset = 0
    while True:
        try:
            data = tg_api(token, "getUpdates",
                          {"timeout": 25, "offset": offset}, timeout=35)
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    tg_handle(token, update["message"])
        except Exception as error:
            print("Telegram error:", error)
            time.sleep(8)


# ======================== battery saver ========================
def battery_loop():
    warned_low = False
    while True:
        time.sleep(30)
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                continue
            low = (not battery.power_plugged
                   and battery.percent <= BATTERY_SAVER_PERCENT)
            if low and not warned_low:
                warned_low = True
                if ptt_vk():
                    state["ptt_only"] = True
                    announce_queue.put(
                        "Battery is at %d percent. To save power I'll stop "
                        "listening all the time. Hold the push to talk key "
                        "when you need me." % battery.percent)
                else:
                    announce_queue.put("Battery is at %d percent, %s. "
                                       "Consider plugging in."
                                       % (battery.percent, USER_NAME))
            elif (battery.power_plugged
                  or battery.percent > BATTERY_SAVER_PERCENT + 5):
                if warned_low:
                    warned_low = False
                    if state["ptt_only"]:
                        state["ptt_only"] = False
                        announce_queue.put("Power restored. Back to "
                                           "listening normally.")
        except Exception as error:
            print("Battery check failed:", error)


# ======================== command routing ========================
def quick_reply(t, words):
    n = USER_NAME
    tokens = t.split()
    if len(tokens) <= 4 and (tokens[:2] == ["thank", "you"]
                             or tokens[0] in ("thanks", "thankyou", "cheers")):
        return "My pleasure, %s." % n
    if len(tokens) <= 6 and ("who are you" in t or "your name" in t):
        return ("I am Optimus, your personal assistant, running right here "
                "on your laptop.")
    if len(tokens) <= 6 and "how are you" in t:
        return "All systems running smoothly, %s. Thank you for asking." % n
    return None


def do_command(text):
    """Returns a reply (text, list or action tuple), or None to ask the AI."""
    global THRESHOLD
    t = normalize_text(text)
    words = [w for w in t.split() if w not in FILLERS]
    if not words:
        return None
    verb, rest = words[0], words[1:]
    short = len(words) <= 7
    if ("what can you do" in t or "your abilities" in t
            or "your features" in t):
        return ("I can open and close apps, folders and files, set timers "
                "and reminders, check the weather and news, search the web, "
                "see your screen, take and find screenshots, type and browse "
                "for you, control music, volume and brightness, keep notes "
                "and a to-do list, and chat about almost anything.")
    reply = quick_reply(t, words)
    if reply:
        return reply
    if "recalibrate" in words or "calibrate" in words:
        say("Recalibrating. Please stay quiet for a moment.")
        wait_speech()
        THRESHOLD = MIC_THRESHOLD or calibrate()
        return "Done. Microphone sensitivity updated."
    if "refresh" in words and any(w in words for w in ("files", "index")):
        threading.Thread(target=refresh_index, daemon=True).start()
        return "Refreshing my file index."
    if any(p in t for p in ("mic check", "microphone check", "test my mic",
                            "test the mic", "test my microphone",
                            "check my microphone", "check my mic")):
        return mic_check()
    if any(p in t for p in ("check my brain", "is ollama running",
                            "restart my brain", "wake your brain",
                            "check ollama")):
        return brain_status()
    for handler in (orb_command, vocab_command):
        reply = handler(t, words)
        if reply:
            return reply
    if any(p in t for p in ("learn my voice", "train my voice",
                            "remember my voice", "enroll my voice",
                            "voice training")):
        return ("enroll",)
    for handler in (voice_lock_command, voice_style_command):
        reply = handler(t, words)
        if reply:
            return reply
    if "code red" in t:
        return ("codered",)
    if "dictation" in words or t in ("dictate", "start dictating"):
        if any(w in words for w in ("stop", "end", "finish", "off")):
            dictation["on"] = False
            return "Dictation off."
        dictation["on"] = True
        return ("Dictation on. Click where you want the text, then just "
                "speak. Say stop dictation when you're done.")
    reply = power_command(t, words)
    if reply:
        return reply
    for handler in (mode_command, focus_command, gaming_command):
        reply = handler(t, words)
        if reply:
            return reply
    for handler in (memory_command, notes_command, todo_command):
        reply = handler(t)
        if reply:
            return reply
    if ((t.startswith("good morning") and len(words) <= 3)
            or any(p in t for p in ("morning briefing", "brief me",
                                    "daily briefing", "my briefing",
                                    "what s my day", "what is my day"))):
        say(ack())
        return briefing_lines()
    reply = alarms_command(t)
    if reply is not None:
        return reply
    if verb in ("minimize", "minimise") and len(rest) <= 4:
        return minimize_command(rest)
    if verb in ("force", "kill") and len(rest) <= 5:
        target = rest[1:] if rest and rest[0] in CLOSE_VERBS else rest
        return close_window_command(target, force=True)
    question = screen_question(t, words)
    if question:
        return ("screen", question)
    reply = screenshot_command(t, words)
    if reply is not None:
        return reply
    if len(words) <= 15:
        reply = browser_command(t, words)
        if reply is not None:
            return reply
    reply = media_command(t, words)
    if reply is not None:
        return reply
    if verb in OPEN_VERBS and len(rest) <= 5:
        return open_target(rest)
    if verb in CLOSE_VERBS and len(rest) <= 4:
        return close_window_command(rest)
    m = re.match(CITY_RE, t) or re.match(r"^i live in\s+(.+)$", t)
    if m:
        city = m.group(1).strip()
        _loc_cache.clear()
        save_setting("city", city)
        return "Got it, %s. I'll use %s for the weather." % (
            USER_NAME, city.title())
    reply = summarize_command(t, words)
    if reply is not None:
        return reply
    query = research_query(t)
    if query:
        if any(w in GOOGLE_HINTS for w in query.split()):
            webbrowser.open("https://www.google.com/search?q="
                            + urllib.parse.quote_plus(query))
            return "Here are the search results for " + query + "."
        return ("research", query, t.startswith("browse"))
    if short and any(w in words for w in WEATHER_TRIGGERS):
        say(ack())
        return weather_command(t, words)
    if short and any(w in words for w in ("news", "headlines")):
        say(ack())
        return news_report(words)
    reply = system_command(t, words)
    if reply is not None:
        return reply
    if short and "battery" in words:
        return battery_status()
    if short and "status" in words:
        return system_status()
    if short and "lock" in words and any(
            w in words for w in ("computer", "laptop", "screen", "pc")):
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "Locking the screen."
    if "time" in words and len(words) <= 5:
        return "It is " + datetime.now().strftime("%I:%M %p").lstrip("0")
    if "date" in words and len(words) <= 6:
        return "Today is " + datetime.now().strftime("%A, %d %B %Y")
    return None


def ends_with_phrase(command, phrases, max_words=8):
    if len(command.split()) > max_words:
        return False
    for p in phrases:
        if (command == p or command.startswith(p + " ")
                or command.endswith(" " + p)):
            return True
    return False


def is_end(command):
    return command in END_EXACT or ends_with_phrase(command, END_PHRASES)


# ======================== the AI brain ========================
def build_system_prompt():
    now = datetime.now()
    parts = [PERSONA, "Right now it is %s." % now.strftime(
        "%A, %d %B %Y, %I:%M %p")]
    mode_text = MODES.get(settings.get("mode", "normal"), "")
    if mode_text:
        parts.append(mode_text)
    if current_style() == "friendly":
        parts.append("Keep your tone warm, cheerful and encouraging, like a "
                     "close friend who is happy to see the user.")
    if quiz["topic"]:
        parts.append("You are quizzing the user on %s. Ask ONE short "
                     "question at a time. After their answer, say whether it "
                     "is right, explain briefly, then ask the next question. "
                     "Keep going until they say stop." % quiz["topic"])
    memory = memory_text()
    if memory:
        parts.append("Things the user asked you to remember: " + memory + ".")
    if my_city():
        parts.append("The user lives near %s." % my_city())
    if news_cache["titles"]:
        parts.append("Recent headlines, mention them only if relevant or "
                     "asked: " + " | ".join(news_cache["titles"]) + ".")
    return " ".join(parts)


def key_text():
    try:
        with open(KEY_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def online_ready():
    return bool(key_text()) and time.time() > online_state["fail_until"]


def warm_up():
    try:
        ensure_ollama()
        body = json.dumps({"model": OLLAMA_MODEL,
                           "keep_alive": BRAIN_KEEP_ALIVE}).encode("utf-8")
        request = urllib.request.Request(
            "http://localhost:11434/api/generate", data=body,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=120).read()
    except Exception as error:
        print("Brain warm-up skipped:", error)


def split_stream(chunks, collected):
    """Turn a stream of text pieces into whole sentences."""
    buffer = ""
    for piece in chunks:
        collected.append(piece)
        buffer += piece
        while True:
            match = re.search(r"(.+?[.!?])\s+", buffer, re.S)
            if not match:
                break
            yield match.group(1).strip()
            buffer = buffer[match.end():]
    if buffer.strip():
        yield buffer.strip()


def local_chunks(system, messages):
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": True,
        "keep_alive": BRAIN_KEEP_ALIVE,
        "options": {"num_predict": 200, "num_ctx": 3072,
                    "temperature": 0.8},
    }).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/chat", data=body,
        headers={"Content-Type": "application/json"})
    with open_ollama(request, 90) as response:
        for line in response:
            if line.strip():
                yield json.loads(line).get("message", {}).get("content", "")


def stream_anthropic(payload, search=False):
    if search:
        payload["tools"] = [{"type": "web_search_20250305",
                             "name": "web_search", "max_uses": 2}]

    def post(body):
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode("utf-8"),
            headers={"x-api-key": key_text(),
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        return urllib.request.urlopen(request, timeout=60)

    try:
        response = post(payload)
    except urllib.error.HTTPError as error:
        if search and error.code == 400:
            payload.pop("tools", None)
            response = post(payload)
        else:
            raise
    with response:
        for raw in response:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            try:
                data = json.loads(line[5:].strip())
            except ValueError:
                continue
            kind = data.get("type")
            if kind == "content_block_delta":
                delta = data.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield delta.get("text", "")
            elif kind == "error":
                raise RuntimeError(str(data.get("error")))


def online_chunks(system, messages, search):
    payload = {"model": ONLINE_MODEL, "max_tokens": 320, "stream": True,
               "system": system, "messages": messages}
    return stream_anthropic(payload, search)


def ask_brain(question, context="", note=None):
    """Yields the answer one sentence at a time."""
    global history
    history.append({"role": "user", "content": question})
    history = history[-12:]
    while history and history[0]["role"] != "user":
        history.pop(0)
    system = build_system_prompt()
    if context:
        system += " " + (note or RESEARCH_NOTE) + " Text: " + context
    collected = []
    started = False
    try:
        if online_ready():
            try:
                for sentence in split_stream(
                        online_chunks(system, history, ONLINE_WEB_SEARCH),
                        collected):
                    started = True
                    yield sentence
                return
            except Exception as error:
                print("Online brain failed:", error)
                online_state["fail_until"] = time.time() + 300
                if started:
                    return
                collected.clear()
                if not online_state["warned"]:
                    online_state["warned"] = True
                    yield ("My online brain isn't reachable, so I'll use my "
                           "offline one.")
        for sentence in split_stream(local_chunks(system, history),
                                     collected):
            yield sentence
    finally:
        # Runs on success, failure AND when the user interrupts mid-answer,
        # so the conversation memory keeps whatever was actually said.
        said = "".join(collected).strip()
        if said:
            history.append({"role": "assistant", "content": said})
        elif history and history[-1]["role"] == "user":
            history.pop()


def answer_research(query, browse=False):
    say(ack())
    if browse:
        webbrowser.open("https://www.google.com/search?q="
                        + urllib.parse.quote_plus(query))
    context = ""
    if online_ready():
        question = ("Search the web if you need to, then tell me about: %s. "
                    "Keep it to a few short sentences." % query)
    else:
        context = gather_sources(query)
        if not context:
            say("I couldn't reach the internet, so this is from memory.")
        question = ("Tell me about: %s. Keep it to a few short sentences."
                    % query)
    show_subtitle("...")
    say_stream(ask_brain(question, context))


def answer_ask(question, context, kind="doc"):
    """Answer a question about text we already have (clipboard, page, file)."""
    if kind != "none":
        say(ack())
    show_subtitle("...")
    note = DOC_NOTE if kind == "doc" else None
    say_stream(ask_brain(question, context, note))


# ---------- seeing the screen ----------
SCREEN_PRIVACY_GUARD = True   # never look at passwords, banking, cards, IDs

PRIVATE_TITLE_RE = re.compile(
    r"\b(password|passcode|keepass\w*|bitwarden|1password|lastpass|dashlane|"
    r"enpass|nordpass|sign[ -]?in|log[ -]?in|otp|verification code|"
    r"net ?banking|internet banking|bank|paypal|paytm|phonepe|gpay|"
    r"google pay|upi|credit card|debit card|checkout|payment|wallet|"
    r"incognito|inprivate|private browsing|aadhaar|digilocker|income tax|"
    r"private key)\b", re.I)
PRIVATE_TEXT_RES = [
    re.compile(r"\b(enter|confirm|new|current|old|your|forgot)\s+"
               r"(your\s+)?(password|passcode|pin)\b", re.I),
    re.compile(r"\b(password|passwd|pwd)\s*[:=]", re.I),
    re.compile(r"\b(cvv|cvc|otp|one[- ]time (password|passcode|code)|"
               r"verification code|security code)\b", re.I),
    re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),                  # Aadhaar style
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),                    # PAN
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),                  # API keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def luhn_ok(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def looks_sensitive(title, process, text):
    """True if the window or the text on screen looks private."""
    if PRIVATE_TITLE_RE.search("%s %s" % (title or "", process or "")):
        return True
    text = text or ""
    if any(p.search(text) for p in PRIVATE_TEXT_RES):
        return True
    for m in re.finditer(r"(?:\d[ -]?){13,19}", text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):    # a card number
            return True
    return False


def foreground_monitor_box():
    """(left, top, right, bottom) of the monitor you're working on."""
    try:
        import ctypes.wintypes as wt
        front = front_window()
        if not front:
            return None
        u = user32_api()

        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT),
                        ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]

        u.MonitorFromWindow.argtypes = [wt.HWND, wt.DWORD]
        u.MonitorFromWindow.restype = wt.HANDLE
        u.GetMonitorInfoW.argtypes = [wt.HANDLE, ctypes.POINTER(MONITORINFO)]
        hmon = u.MonitorFromWindow(front[0], 2)      # nearest monitor
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not hmon or not u.GetMonitorInfoW(hmon, ctypes.byref(info)):
            return None
        r = info.rcMonitor
        return (r.left, r.top, r.right, r.bottom)
    except Exception as error:
        print("Couldn't find the active monitor:", error)
        return None


def capture_screen():
    """The monitor you're working on, retried if it comes out blank.

    Returns (image, blank). blank=True means every attempt was a black or
    single-colour frame (a locked screen or protected video)."""
    from PIL import ImageGrab, ImageStat
    box = foreground_monitor_box()
    img, blank = None, True
    for attempt in range(3):
        try:
            img = ImageGrab.grab(bbox=box, all_screens=True) if box \
                else ImageGrab.grab(all_screens=True)
        except Exception as error:
            print("Screen grab failed:", error)
            img = ImageGrab.grab(all_screens=True)
        img = img.convert("RGB")
        if ImageStat.Stat(img.convert("L")).stddev[0] > 1.5:
            blank = False
            break
        time.sleep(0.4)
    return img, blank


def screen_image_b64(img, max_side=1600):
    import base64
    import io
    from PIL import Image
    scale = min(1.0, max_side / float(max(img.size)))
    if scale < 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)),
                         Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def ocr_image(img):
    """The text on the screen, or None if the reader isn't available."""
    try:
        if _ocr["engine"] is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                _ocr["engine"] = RapidOCR()
            except Exception:
                _ocr["engine"] = False
        if not _ocr["engine"]:
            return None
        result, _ = _ocr["engine"](np.array(img))
        return " ".join(r[1] for r in (result or []))
    except Exception as error:
        print("Screen text reading failed:", error)
        return None


def vision_local_chunks(system, question, image_b64):
    body = json.dumps({
        "model": VISION_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": question,
                      "images": [image_b64]}],
        "stream": True, "keep_alive": "10m",
        "options": {"num_predict": 220, "num_ctx": 4096,
                    "temperature": 0.6},
    }).encode("utf-8")
    request = urllib.request.Request(
        "http://localhost:11434/api/chat", data=body,
        headers={"Content-Type": "application/json"})
    with open_ollama(request, 120) as response:
        for line in response:
            if line.strip():
                yield json.loads(line).get("message", {}).get("content", "")


def vision_online_chunks(system, question, image_b64):
    payload = {
        "model": ONLINE_MODEL, "max_tokens": 400, "stream": True,
        "system": system,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": "image/jpeg",
                                         "data": image_b64}},
            {"type": "text", "text": question}]}],
    }
    return stream_anthropic(payload, False)


def answer_screen(question):
    try:
        img, blank = capture_screen()
    except Exception as error:
        print("Screen capture failed:", error)
        say("I couldn't capture the screen, %s." % USER_NAME)
        return
    say(ack())
    show_subtitle("...")
    set_orb("thinking")
    if blank:
        say("Your screen is coming through completely black, %s. That "
            "usually means a locked screen or a protected video." % USER_NAME)
        return
    front = front_window()
    title, proc = (front[3], front[2]) if front else ("", "")
    text = run_with_timeout(ocr_image, (img,), 12)
    if text is _TIMEOUT:
        text = None
    if SCREEN_PRIVACY_GUARD and looks_sensitive(title, proc, text):
        print("Screen skipped: looks private (%s)" % title)
        say("That looks private, %s, so I'm not going to look at it. Ask me "
            "again once it's off the screen." % USER_NAME)
        return
    image = screen_image_b64(img)
    system = (build_system_prompt() + " The user has shared a screenshot of "
              "their screen. It is attached to this message and it is NOT "
              "empty, so never say the screen is empty or that you can't "
              "see it; say what you can make out, even if it is partial. "
              "Describe or explain what matters for their request in a few "
              "short spoken sentences. Read out important text only if "
              "asked, and never read out passwords, card numbers or codes.")
    ask = question
    if text:
        ask += ("\n\nText detected on the screen (may contain small "
                "mistakes):\n" + text[:2500])
    collected = []
    sources = []
    if online_ready():
        sources.append(("online", lambda: vision_online_chunks(
            system, ask, image)))
    sources.append(("local", lambda: vision_local_chunks(
        system, ask, image)))
    for name, make in sources:
        spoke = False
        try:
            stream = split_stream(make(), collected)
            for sentence in stream:
                if interrupted():
                    stream.close()
                    break
                spoke = True
                say(clean(sentence))
            break
        except urllib.error.HTTPError as error:
            print("Vision (%s) failed: %s" % (name, error))
            if name == "local":
                say("My vision model isn't ready. Please run ollama pull "
                    + VISION_MODEL)
        except Exception as error:
            print("Vision (%s) failed: %s" % (name, error))
            if name == "local":
                say("I couldn't look at the screen right now.")
        if spoke:
            break
    answer = "".join(collected).strip()
    if answer:
        history.append({"role": "user",
                        "content": "[I showed you my screen] " + question})
        history.append({"role": "assistant", "content": answer})


# ======================== tray icon ========================
def make_tray_image(muted=False):
    """The little icon next to the clock: your logo inside a glowing ring."""
    from PIL import Image, ImageDraw, ImageEnhance
    big = 256
    ring = (110, 110, 110, 255) if muted else (139, 111, 208, 255)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((4, 4, big - 5, big - 5),
                                fill=(8, 20, 32, 255), outline=ring, width=14)
    try:
        logo = prepare_logo(current_logo_path())
        logo = logo.resize((190, 190), Image.LANCZOS)
        if muted:
            rgb = ImageEnhance.Brightness(logo.convert("RGB")).enhance(0.5)
            rgb.putalpha(logo.getchannel("A"))
            logo = rgb
        img.alpha_composite(logo, ((big - 190) // 2, (big - 190) // 2))
    except Exception as error:
        print("Tray icon logo unavailable, using a plain dot:", error)
        ImageDraw.Draw(img).ellipse((88, 88, 168, 168), fill=ring)
    return img.resize((64, 64), Image.LANCZOS)


def start_tray():
    try:
        import pystray
        from PIL import Image, ImageDraw

        tray_ref["on"] = make_tray_image(False)
        tray_ref["off"] = make_tray_image(True)

        def toggle_mute(icon, item):
            state["muted"] = not state["muted"]
            icon.icon = tray_ref["off"] if state["muted"] else tray_ref["on"]
            icon.title = "Optimus (muted)" if state["muted"] else "Optimus"

        def open_control_panel(icon, item):
            orb_cmds.put(("panel",))

        def toggle_lock(icon, item):
            save_setting("voice_lock", not lock_enabled())

        def stop_talking(icon, item):
            stop_speaking()

        def abort_shutdown(icon, item):
            subprocess.run(["shutdown", "/a"], capture_output=True)

        def quit_app(icon, item):
            try:
                icon.stop()
            finally:
                os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open control panel", open_control_panel,
                             default=True),
            pystray.MenuItem("Mute Optimus", toggle_mute,
                             checked=lambda item: state["muted"]),
            pystray.MenuItem("Voice lock", toggle_lock,
                             checked=lambda item: lock_enabled()),
            pystray.MenuItem("Stop speaking", stop_talking),
            pystray.MenuItem("Abort shutdown", abort_shutdown),
            pystray.MenuItem("Quit Optimus", quit_app))
        tray_ref["icon"] = pystray.Icon("Optimus", tray_ref["on"], "Optimus",
                                        menu)
        tray_ref["icon"].run_detached()
    except Exception as error:
        print("Tray icon unavailable:", error)


# ======================== start up and main loop ========================
def handle_reply(reply, command):
    if reply is _TIMEOUT:
        say("That is taking longer than expected, " + USER_NAME
            + ". Please try again in a moment.")
    elif reply is None:
        set_orb("thinking")
        show_subtitle("...")
        say_stream(ask_brain(command))
    elif isinstance(reply, tuple):
        kind = reply[0]
        if kind == "research":
            answer_research(reply[1], reply[2])
        elif kind == "ask":
            answer_ask(reply[1], reply[2], reply[3])
        elif kind == "screen":
            answer_screen(reply[1])
        elif kind == "enroll":
            enroll_voice()
        elif kind == "codered":
            code_red()
        elif kind == "confirm":
            if confirm(reply[2]):
                run_action(reply[1])
            else:
                say("Cancelled.")
    elif isinstance(reply, list):
        for sentence in reply:
            say(sentence)
    else:
        say(reply)


def brain_error_detail(error):
    """What the AI server actually said was wrong (short)."""
    try:
        body = error.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    return (body or str(error)).strip()[:300]


def process_command(command):
    """Run one command, spoken or typed. Returns False when the chat ends."""
    command = expand_phrase(command)
    if (ends_with_phrase(command, SHUTDOWN_PHRASES, 3)
            and not any(w in command.split() for w in PC_WORDS)):
        say(farewell())
        wait_speech()
        os._exit(0)
    if is_end(command):
        say(farewell())
        wait_speech()
        return False
    reply_epoch["n"] = stop_epoch["n"]   # a later stop cancels THIS reply
    working["on"] = True
    try:
        reply = run_with_timeout(do_command, (command,), 45)
        handle_reply(reply, command)
    except urllib.error.HTTPError as error:
        if history and history[-1]["role"] == "user":
            history.pop()
        detail = brain_error_detail(error)
        print("Brain error %s: %s" % (error.code, detail))   # the real reason
        if error.code == 404:
            say("My brain model is missing. Please run ollama pull "
                + OLLAMA_MODEL)
        elif "memory" in detail.lower():
            say("My offline brain ran out of memory, %s. Close a few apps "
                "and ask me again." % USER_NAME)
        else:
            say("My brain hit a snag. Please try that again.")
    except urllib.error.URLError as error:
        if history and history[-1]["role"] == "user":
            history.pop()
        print("Brain connection error:", error)
        say("My offline brain isn't answering, %s. I tried to wake it, "
            "so please give it a moment and ask again." % USER_NAME)
    except Exception as error:
        print("Something went wrong:", repr(error))
        say("Sorry, something went wrong.")
    wait_speech()
    working["on"] = False
    return True


if __name__ == "__main__":
    if "--make-shortcut" in sys.argv:
        load_settings()
        ensure_logo_pack()
        for kind, where in (("Desktop", "the desktop"),
                            ("Programs", "the Start menu")):
            try:
                create_shortcut(kind)
                print("Optimus icon added to %s." % where)
            except Exception as error:
                print("Couldn't add the icon to %s: %s" % (where, error))
        sys.exit(0)
    if "--import-logos" in sys.argv:
        load_settings()
        try:
            picture = sys.argv[sys.argv.index("--import-logos") + 1]
            found = split_logo_sheet(picture)
            print("Imported %d logos: %s" % (len(found), ", ".join(
                label for label, rel in found)))
        except Exception as error:
            print("Couldn't import the logo sheet:", error)
        sys.exit(0)
    threading.excepthook = lambda a: log_problem(
        "background task " + str(getattr(a.thread, "name", "")),
        (a.exc_type, a.exc_value, a.exc_traceback))
    if already_running():
        if not tell_running_copy():
            show_message("Optimus looks like it is already running, but it "
                         "is not answering.\n\nRight-click its tray icon "
                         "(near the clock) and choose Quit, or end "
                         "'pythonw.exe' / 'python.exe' in Task Manager, then "
                         "start Optimus again.")
        sys.exit(0)
    stop_other_copies()         # an older Optimus must not keep running
    load_settings()
    ensure_logo_pack()
    threading.Thread(target=refresh_shortcuts, daemon=True).start()
    threading.Thread(target=ipc_server, daemon=True).start()
    threading.Thread(target=hotkey_loop, daemon=True).start()
    threading.Thread(target=overlay_loop, daemon=True).start()
    threading.Thread(target=ensure_logo_pack, daemon=True).start()
    start_tray()

    print("Loading the voice...")
    try:
        from kokoro_onnx import Kokoro
        tts = Kokoro(MODEL_PATH, VOICES_PATH)
    except Exception as error:
        print("Natural voice unavailable, using the basic voice:", error)
    threading.Thread(target=synth_worker, daemon=True).start()
    threading.Thread(target=play_worker, daemon=True).start()
    threading.Thread(target=interrupt_watcher, daemon=True).start()
    say(greeting())  # plays while the rest of Optimus loads

    print("Loading the ears...")
    model = load_whisper()
    if WAKE_MODEL:
        try:
            wake_model = WhisperModel(WAKE_MODEL, device="cpu",
                                      compute_type="int8")
        except Exception as error:
            print("Quick wake model unavailable:", error)
    load_speaker()

    print("Finding your apps...")
    APPS = load_apps()
    load_cache()
    load_alarms()
    load_shots()
    threading.Thread(target=refresh_index, daemon=True).start()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    threading.Thread(target=warm_up, daemon=True).start()
    threading.Thread(target=news_loop, daemon=True).start()
    threading.Thread(target=ollama_watchdog, daemon=True).start()
    threading.Thread(target=battery_loop, daemon=True).start()
    threading.Thread(target=telegram_loop, daemon=True).start()

    wait_speech()
    select_microphone()
    print("Waiting for the microphone...")
    wait_for_microphone()
    print("Stay quiet for a moment...")
    THRESHOLD = MIC_THRESHOLD or calibrate()
    print("Mic sensitivity:", round(THRESHOLD, 4))

    if (speaker["extractor"] is not None and speaker["print"] is None
            and not settings.get("lock_hint_given")):
        save_setting("lock_hint_given", True)
        say("When you're ready, say: learn my voice, and I'll answer only "
            "to you.")
        wait_speech()
    today = datetime.now().strftime("%Y-%m-%d")
    if (AUTO_BRIEFING and 5 <= datetime.now().hour < 12
            and settings.get("last_briefing") != today):
        lines = run_with_timeout(briefing_lines, (), 45)
        if isinstance(lines, list):
            for line in lines:
                say(line)
            wait_speech()

    active = True  # the greeting asked a question, so listen for the answer
    last_reject = 0.0
    force_listen = False
    while True:
        process_announcements()
        if not wake_queue.empty():
            while True:
                try:
                    wake_queue.get_nowait()
                except queue.Empty:
                    break
            state["muted"] = False
            stop_speaking()
            say("Yes, " + USER_NAME + "?")
            wait_speech()
            active = True
            force_listen = True
            continue
        if not typed_queue.empty():
            # a command typed in the control panel: same path as your voice
            try:
                typed_text, typed_speak = typed_queue.get_nowait()
            except queue.Empty:
                typed_text, typed_speak = "", True
            typed_command = typed_to_command(typed_text)
            if typed_command:
                stop_speaking()
                state["quiet"] = (not typed_speak) or state["muted"]
                try:
                    active = process_command(typed_command)
                finally:
                    state["quiet"] = False
            continue
        if state["muted"]:
            set_orb("muted")
            active = False
            time.sleep(0.3)
            continue
        ptt_down = ptt_pressed()
        if state["ptt_only"] and not ptt_down and not force_listen:
            set_orb("idle")
            time.sleep(0.1)
            continue
        force_listen = False
        set_orb("idle")
        try:
            if ptt_down:
                audio = record_while_key(ptt_vk())
            else:
                audio = record_until_silence(
                    wait_seconds=(FOLLOWUP_SECONDS
                                  if active and not dictation["on"]
                                  else None),
                    interrupt=lambda: (not announce_queue.empty()
                                       or not wake_queue.empty()
                                       or not typed_queue.empty()
                                       or state["muted"]
                                       or state["ptt_only"]
                                       or ptt_pressed()))
        except Exception as error:
            print("Microphone problem:", error)
            try:
                sd._terminate()
                sd._initialize()
            except Exception:
                pass
            time.sleep(3)
            continue
        if audio is None:
            if not ptt_down:
                active = False
            continue
        direct = ptt_down or active or dictation["on"]
        if not direct and wake_model is not None:
            quick, _ = transcribe(wake_model, audio, prompt="Optimus.",
                                  beam=1, strict=False)
            if find_wake_word(quick.split()) == -1:
                continue
        if not speaker_ok(audio):
            if not direct and time.time() - last_reject > 20:
                last_reject = time.time()
                say("Voice not recognised.")
                wait_speech()
            continue
        set_orb("thinking")
        text, raw = transcribe(model, audio)
        if not text:
            continue
        print("Heard:", text)
        log_event("heard", text)
        if dictation["on"]:
            handle_dictation(raw, text)
            continue
        words = text.split()
        i = find_wake_word(words)
        if i != -1:
            words = words[:i] + words[i + 1:]
        elif not direct:
            continue
        command = " ".join(words)
        if not command:
            say("Yes, " + USER_NAME + "?")
            wait_speech()
            active = True
            continue
        active = process_command(command)
