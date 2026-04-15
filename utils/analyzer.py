import difflib
import random
import re

DEFAULT_PRACTICE_SENTENCES = {
    "easy": [
        "The sun is shining brightly today.",
        "I enjoy reading books in the park.",
        "Please pass the salt and pepper.",
    ],
    "medium": [
        "My favorite season is autumn because of the cool breeze.",
        "The city skyline looks beautiful at sunset.",
        "She practices English every morning before work.",
    ],
    "hard": [
        "The craftsmanship of the antique clock amazed the visitors.",
        "He understood the significance of extraordinary persistence.",
        "Their conversation explored the philosophy of language.",
    ],
}

_PRONUNCIATION_TIPS = {
    "think": "Use the soft /θ/ sound, not /t/.",
    "through": "Try a gentle /θ/ and keep the vowel long.",
    "though": "Make the /ð/ sound with your tongue between your teeth.",
    "pronunciation": "Break it into syllables: pro-nun-ci-a-tion.",
    "comfortable": "Say it as 'COMF-ter-bull', not 'com-for-ta-ble'.",
    "schedule": "In American English, use /skedʒʊl/.",
    "vegetable": "Remember the middle syllable is very light.",
    "specific": "Stress the second syllable: spe-CIF-ic.",
    "library": "Say it as 'LYE-brer-ee'.",
    "interesting": "Try 'IN-trest-ing'.",
}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s']", "", text)
    return text


def tokenize(text: str) -> list[str]:
    cleaned = normalize(text)
    return [token for token in cleaned.split() if token]


def compare_texts(reference: str, spoken: str) -> dict:
    ref_words = tokenize(reference)
    spoken_words = tokenize(spoken)
    matcher = difflib.SequenceMatcher(None, ref_words, spoken_words)

    wrong_words = []
    colored_segments = []

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "equal":
            for word in ref_words[i1:i2]:
                colored_segments.append({"word": word, "state": "correct"})
        else:
            for word in ref_words[i1:i2]:
                colored_segments.append({"word": word, "state": "wrong"})
                wrong_words.append(word)

    matched = sum(
        len(ref_words[i1:i2])
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes()
        if opcode == "equal"
    )
    accuracy = round((matched / len(ref_words)) * 100) if ref_words else 0

    colored_html = " ".join(
        f'<span class="word {segment["state"]}">{segment["word"]}</span>'
        for segment in colored_segments
    )

    return {
        "accuracy": accuracy,
        "colored_html": colored_html,
        "wrong_words": wrong_words,
        "reference_words": ref_words,
        "spoken_words": spoken_words,
        "transcript": spoken,
    }


def get_pronunciation_tip(wrong_words: list[str], difficulty: str = "easy") -> str:
    if not wrong_words:
        return "Excellent! Your pronunciation matched the sentence well."

    unique_words = []
    for word in wrong_words:
        if word not in unique_words:
            unique_words.append(word)

    tips = []
    for word in unique_words[:4]:
        normalized = word.lower()
        if normalized in _PRONUNCIATION_TIPS:
            tips.append(f"{word}: {_PRONUNCIATION_TIPS[normalized]}")
        else:
            tips.append(f"Try pronouncing '{word}' more clearly.")

    if difficulty == "hard":
        tips.append("Focus on pacing, syllable stress, and consonant clarity.")
    elif difficulty == "medium":
        tips.append("Practice slowly and repeat the sentence until it feels more natural.")
    else:
        tips.append("Listen for each word, and try again with calm breathing.")

    return " ".join(tips)


def suggest_daily_sentence(sentences: dict[str, list[str]]) -> dict:
    difficulty = random.choice(["easy", "medium", "hard"])
    sentence = random.choice(sentences[difficulty])
    return {"difficulty": difficulty, "sentence": sentence}
