"""One wrapper for every Gemini call. Returns None when no API key or the call fails,
so every caller has an offline fallback."""
import io
import json
import os
import re
import wave

from dotenv import load_dotenv

load_dotenv()
_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
_MODELS = [m for m in [os.getenv("GEMINI_MODEL"), "gemini-3.5-flash", "gemini-2.5-flash"] if m]
_client = None


def available():
    return bool(_KEY)


def _get():
    global _client
    if _client is None and _KEY:
        from google import genai
        _client = genai.Client(api_key=_KEY)
    return _client


def _call(contents, as_json=False, temperature=0.5):
    client = _get()
    if not client:
        return None
    from google.genai import types
    cfg = types.GenerateContentConfig(temperature=temperature,
                                      response_mime_type="application/json" if as_json else None)
    for model in _MODELS:
        try:
            return client.models.generate_content(model=model, contents=contents, config=cfg).text
        except Exception as e:  # try the next model name
            print(f"[llm] {model} failed: {e}")
    return None


def text(prompt, temperature=0.6):
    return _call(prompt, temperature=temperature)


def json_out(prompt, temperature=0.4):
    raw = _call(prompt, as_json=True, temperature=temperature)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}|\[.*\]", raw, re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def transcribe(audio_bytes, mime="audio/wav"):
    if not available():
        return None
    from google.genai import types
    part = types.Part.from_bytes(data=audio_bytes, mime_type=mime)
    out = _call([part, "Transcribe this interview answer word for word, keeping filler words like 'umm'. "
                       "Return only the transcript."], temperature=0)
    return out.strip() if out else None


def wav_seconds(audio_bytes):
    try:
        with wave.open(io.BytesIO(audio_bytes)) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None
