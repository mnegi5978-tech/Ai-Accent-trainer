import base64
import datetime
import os
import tempfile
import uuid
from typing import Optional

from flask import Flask, jsonify, render_template, request, session

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from utils.analyzer import (
    DEFAULT_PRACTICE_SENTENCES,
    compare_texts,
    get_pronunciation_tip,
    suggest_daily_sentence,
)
from utils.speech import recognize_audio

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "accent_trainer_dev_secret")

AUDIO_FOLDER = os.path.join(app.root_path, "static", "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def init_progress():
    if "practice_count" not in session:
        session["practice_count"] = 0
    if "best_score" not in session:
        session["best_score"] = 0
    if "history" not in session:
        session["history"] = []


@app.route("/")
def home():
    init_progress()

    daily_sentence = suggest_daily_sentence(DEFAULT_PRACTICE_SENTENCES)

    return render_template(
        "index.html",
        practice_sentences=DEFAULT_PRACTICE_SENTENCES,
        daily_sentence=daily_sentence,
        progress={
            "practice_count": session["practice_count"],
            "best_score": session["best_score"],
            "history": session["history"],
        },
    )


@app.route("/record", methods=["POST"])
def record_audio():
    data = request.get_json(force=True)
    audio_base64 = data.get("audioBase64")

    if not audio_base64:
        return jsonify({"success": False, "message": "Audio data missing."}), 400

    try:
        if audio_base64.startswith("data:"):
            audio_base64 = audio_base64.split(",", 1)[1]
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return jsonify({"success": False, "message": "Could not decode audio."}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name

    try:
        transcript = recognize_audio(temp_path)
        if transcript is None:
            transcript = ""
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return jsonify({"success": True, "transcript": transcript})


@app.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json(force=True)
    original = data.get("sentence", "").strip()
    transcript = data.get("transcript", "").strip()
    difficulty = data.get("difficulty", "easy")

    if not original:
        return jsonify({"success": False, "message": "Please enter or select a sentence."}), 400

    result = compare_texts(original, transcript)
    result["pronunciation_tip"] = get_pronunciation_tip(result["wrong_words"], difficulty)

    session["practice_count"] += 1
    session["best_score"] = max(session["best_score"], result["accuracy"])
    session["history"].insert(
        0,
        {
            "sentence": original,
            "score": result["accuracy"],
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    )
    session["history"] = session["history"][:10]

    audio_url = None

    def save_tts_audio(text: str) -> Optional[str]:
        if gTTS is not None:
            try:
                filename = f"pronunciation_{uuid.uuid4().hex}.mp3"
                path = os.path.join(AUDIO_FOLDER, filename)
                tts = gTTS(text=text, lang="en")
                tts.save(path)
                return filename
            except Exception:
                pass

        if pyttsx3 is not None:
            try:
                filename = f"pronunciation_{uuid.uuid4().hex}.wav"
                path = os.path.join(AUDIO_FOLDER, filename)
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.save_to_file(text, path)
                engine.runAndWait()
                return filename
            except Exception:
                pass

        return None

    audio_filename = save_tts_audio(original)
    if audio_filename:
        audio_url = f"/static/audio/{audio_filename}"

    result["audio_url"] = audio_url
    result["success"] = True
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
