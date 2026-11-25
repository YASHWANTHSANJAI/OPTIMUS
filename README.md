# OPTIMUS

**A voice assistant for Windows with a floating logo orb, a full control panel and a cinematic, Marvel-inspired look.**

Say "Optimus", ask for something, and it answers out loud. It runs mostly on your own PC (local speech recognition, local voices, a local AI model through Ollama), and can optionally use Claude when you add an API key.

> Status: personal project, actively developed. Windows only.

---

## Contents
1. [Features](#features)
2. [How it works](#how-it-works)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [First run](#first-run)
6. [Using Optimus](#using-optimus)
7. [The control panel](#the-control-panel)
8. [Settings and customisation](#settings-and-customisation)
9. [Hotkeys](#hotkeys)
10. [Optional extras](#optional-extras)
11. [Files Optimus creates](#files-optimus-creates)
12. [Troubleshooting](#troubleshooting)
13. [Privacy](#privacy)
14. [Project layout and roadmap](#project-layout-and-roadmap)
15. [Credits and licence](#credits-and-licence)

---

## Features

**Voice**
- Wake word ("Optimus") or a hold-to-talk key
- Local speech recognition with faster-whisper
- Natural voices with Kokoro, with 16 built-in voice packs and effects
- Adjustable microphone sensitivity, speaking speed and voice style
- Stop Optimus mid-sentence by tapping your talk key
- Optional **voice lock**: only your voice is accepted (sherpa-onnx speaker model)

**Brain**
- Local AI through Ollama, no cloud needed
- Optional online brain with Claude (add an API key file)
- Built-in skills: time, weather, timers and alarms, to-do list, notes and memory, screenshots, battery and system status, opening apps and files, media and volume control, web search and news

**Screen awareness**
- Take a screenshot and ask "what's on my screen?" (OCR reads the text for you)

**Floating orb**
- Always-on-top, click-through-safe logo orb you can drag and resize
- Reacts to state: idle, listening, thinking, speaking, muted
- Voice waves, orbit sparks, particles and ripples
- 14 colour themes, a drifting Spectrum theme, and a Custom theme with your own two colours
- Per-mood colours, ring style, logo size, spin, bounce, opacity and more

**Control panel**
- Black and matte-purple minimalist design with a customisable accent colour
- Console (type commands), Emblems, Orb, Cursor, Voice, Hotkeys, Presets and Settings pages
- Draggable scroll bar, smooth page transitions, quiet quote line

**Emblems**
- Built-in original emblem pack
- Add your own PNG/JPG logos, or import a whole sheet of logos on a white background and it cuts them apart automatically
- The chosen emblem becomes your orb, tray icon, window icon and desktop icon

**Cinematic screen effects ("Assemble")**
- Five full-screen scenes drawn in your orb colours: Vibranium Pulse, Hex Grid, Cinema Title, Orbit Lock, Converge
- Plays from the Assemble button, a hotkey, or at startup

**Cursor**
- Optional hero pointer and trail effects, only inside Optimus windows by default

**Shortcuts and automation**
- Global hotkeys for any action
- Custom missions: a key combination that runs any command
- Custom phrases: say a short phrase to run a longer command
- Presets that apply a theme, voice, orbit and mode in one click

**App feel**
- Desktop, Start menu and startup shortcuts from inside the panel
- Launching it a second time simply opens the running copy's control panel

---

## How it works

```
 microphone ──► voice detection ──► faster-whisper (speech to text)
                                          │
                       (optional) voice lock check (sherpa-onnx)
                                          │
                                          ▼
                    command router ── built-in skills (time, apps, files…)
                                          │ otherwise
                                          ▼
                       brain: Ollama (local)  or  Claude (online, optional)
                                          │
                                          ▼
                     Kokoro text to speech ──► speakers
                                          │
                        orb + panel animate with the audio level
```

Everything is in a single Python file for now (`optimus.py`). The user interface runs in Tkinter, the tray icon uses pystray.

---

## Requirements

- Windows 10 or 11
- Python 3.10 or newer (tick "Add Python to PATH" when installing)
- A working microphone and speakers
- About 3 GB of free disk space for models
- Optional: an NVIDIA GPU makes speech recognition faster (CPU works fine)
- Optional: [Ollama](https://ollama.com) for the local brain

---

## Installation

1. **Get the code**
   ```
   git clone https://github.com/YASHWANTHSANJAI/OPTIMUS.git
   cd OPTIMUS
   ```
   (Or download the ZIP from GitHub and unzip it.)

2. **Install the Python packages**
   ```
   pip install -r requirements.txt
   ```

3. **Download the voice files** and put them in the same folder as `optimus.py`:
   - `kokoro-v1.0.onnx` (or the smaller `kokoro-v1.0.int8.onnx`)
   - `voices-v1.0.bin`

   Both come from the kokoro-onnx project's releases page.

4. **(Optional) Voice lock**: put a speaker model named `speaker_model.onnx` in the same folder, then enrol your voice from the assistant.

5. **(Optional) Local brain**: install Ollama, then pull a model, for example:
   ```
   ollama pull llama3.2
   ```

---

## First run

```
python optimus.py
```

- The first start downloads the speech model, so give it a minute.
- The orb appears on screen and a tray icon is added near the clock.
- Say **"Optimus, what time is it?"**, or type the same thing in the panel's Console.
- To add a desktop icon: open the panel, go to **Settings**, and choose the deploy option. Or run:
  ```
  python optimus.py --make-shortcut
  ```

### Command line options

| Option | What it does |
|---|---|
| `--panel` | Opens the control panel on start |
| `--make-shortcut` | Adds Desktop and Start menu shortcuts, then exits |
| `--import-logos "<path>"` | Cuts a sheet of logos into separate emblems, then exits |

---

## Using Optimus

Some things to try:

- "Optimus, what's the weather?"
- "Optimus, set a timer for ten minutes."
- "Optimus, take a screenshot." then "What's on my screen?"
- "Optimus, minimize this window."
- "Optimus, volume up."
- "Optimus, open Chrome."
- "Optimus, remind me to call home at six."
- "Optimus, change your voice to Nova."

You can also type any of these into the panel's Console page. It runs them exactly like your voice.

---

## The control panel

Open it from the tray icon, the orb's right-click menu, or the hotkey.

| Page | What you do there |
|---|---|
| **Console** | Type commands, see the conversation, quick-command buttons |
| **Emblems** | Choose your logo; add your own; import a sheet |
| **Orb** | Orb, Colours, Orbit, Waves, Finish and Screen tabs |
| **Cursor** | Pointer effect, size, trail and click bursts |
| **Voice** | Voice packs, speed, microphone sensitivity, voice lock |
| **Hotkeys** | Talk key, global shortcuts, custom missions, custom phrases |
| **Presets** | One-click combinations of theme, voice and orbit |
| **Settings** | Panel accent colour, shortcuts for the desktop, startup options |

---

## Using your own logos
This public version ships with a small set of original emblems only. To use any picture as your orb: open the control panel, go to **Emblems**, and choose **Add my own logo**. If you have a sheet of several logos on a white background, choose **Import sheet** and Optimus cuts them apart for you.

---

## Settings and customisation

All settings are saved in `settings.json` next to the program. You can change almost everything from the panel, including:

- Orb: style, size, opacity, logo size, spin, bounce, ring style, dust style and amount
- Colours: 14 palettes, Spectrum, Custom, per-mood colours
- Orbit: spark count, speed, size, tail length, shape (dot, diamond, star)
- Voice waves: ring, bars, both or off, plus strength
- Assemble animation: pick one scene, Random, or Off; optionally play one at startup
- Panel: accent colour (Matte Purple, Vibranium Silver, Royal Blue, Emerald, Crimson, Antique Gold, Rose, or Custom), page glide, header shimmer

---

## Hotkeys

Defaults (all changeable in the panel):

| Action | Shortcut |
|---|---|
| Open the control panel | Ctrl + Alt + O |
| Wake Optimus | Ctrl + Alt + W |
| Stop speaking | Ctrl + Alt + S |
| Mute / unmute | Ctrl + Alt + M |
| Take a screenshot | Ctrl + Alt + P |
| Show / hide the flying cursor | Ctrl + Alt + F |
| Voice lock on / off | Ctrl + Alt + L |
| Assemble animation | Ctrl + Alt + A |

The default hold-to-talk key is Right Ctrl.

---

## Optional extras

Create these plain-text files next to `optimus.py`. **Never commit them to Git.** They are already listed in `.gitignore`.

| File | Purpose |
|---|---|
| `api_key.txt` | Your Claude API key, to use the online brain |
| `telegram_token.txt` | Bot token for remote control by Telegram |
| `telegram_secret.txt` | A pairing secret, so only you can pair your Telegram account |

With Telegram set up you can send commands such as `/battery`, `/status`, `/screenshot`, `/lock` and `/say` from your phone.

---

## Files Optimus creates

| File / folder | Contents |
|---|---|
| `settings.json` | Your settings |
| `memory.json`, `todo.json`, `alarms.json` | Notes, to-dos and alarms |
| `voiceprint.npy` | Your enrolled voice for the voice lock |
| `logos/` | Emblem images |
| `optimus.log` | Log output when run without a console |
| `index_cache.json` | Cached index of your files for fast "open X" |

---

## Troubleshooting

- **It doesn't hear me:** raise the microphone sensitivity in the Voice page and check Windows' default input device.
- **It hears itself:** use headphones, and turn on headphones mode.
- **No voice or a robotic voice:** make sure the two Kokoro files are in the same folder as `optimus.py`. Without them it falls back to a basic Windows voice.
- **Ollama errors:** start Ollama first, and confirm a model is installed with `ollama list`.
- **Orb has a black box behind it:** update to the latest version of the file.
- **The custom pointer doesn't change:** the Cursor page shows a status line. If it reports a problem, Optimus falls back to the normal pointer.
- **A second copy won't start:** Optimus allows one copy. Launching again opens the running copy's panel. To restart, right-click the tray icon and choose Quit.
- **Anything else:** look at `optimus.log`.

---

## Privacy

- Speech recognition, voices and the default brain run on your computer.
- Nothing is sent online unless you add an API key (Claude) or turn on Telegram, or ask for something that needs the internet, such as weather or news.
- Your settings, memory and voiceprint stay in the program folder and are excluded from Git.

---

## Project layout and roadmap

Right now everything lives in one file:

```
OPTIMUS/
├─ optimus.py          the whole program
├─ requirements.txt    Python packages
├─ README.md
├─ LICENSE
└─ .gitignore
```

Ideas for later:
- Split the program into modules (voice, brain, orb, panel, hotkeys)
- An installer or one-click setup script
- More skills and plugin support
- Automatic model download on first run

---

## Credits and licence

Built by Yashwanth.

Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx), [Ollama](https://ollama.com), [Pillow](https://python-pillow.org), [pystray](https://github.com/moses-palmer/pystray), and Python's Tkinter.

Released under the [MIT licence](LICENSE).

This is a fan-made personal project. It is not affiliated with, endorsed by or sponsored by Marvel or Disney. Marvel names and artwork belong to their respective owners and are not included in the public version.
