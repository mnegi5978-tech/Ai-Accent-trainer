import speech_recognition as sr


def recognize_audio(wav_path: str) -> str:
    """Recognize spoken English from a WAV file using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
