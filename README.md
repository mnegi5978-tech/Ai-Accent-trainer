# AI Accent Trainer

A polished Flask app for practicing English pronunciation using browser recording, server-side speech recognition, and AI-style feedback.

## Features

- Select or type practice sentences
- Difficulty levels: easy, medium, hard
- Daily practice sentence recommendation
- Browser microphone recording with instant transcription
- Accuracy percentage and highlighted mistakes
- Pronunciation tips for common problem words
- Playback of the correct pronunciation
- Progress tracking with session count, best score, and history

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install project dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python app.py
```

4. Open the app in your browser:

```powershell
http://127.0.0.1:5000
```

## Notes

- The backend uses `SpeechRecognition` with the Google speech API for transcription.
- Pronunciation audio is generated with `gTTS`, with `pyttsx3` as a local fallback.
- If the browser prompts for microphone access, allow it to record your practice audio.
