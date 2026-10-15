"""
utils/voice_helper.py
----------------------
Optional voice input helper using SpeechRecognition.
Falls back gracefully if pyaudio is not installed.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logger.warning("SpeechRecognition not installed. Voice input unavailable.")


def transcribe_from_microphone(timeout: int = 10, phrase_limit: int = 30) -> dict:
    """
    Record audio from the default microphone and transcribe to text.

    Returns
    -------
    dict with keys:
        success (bool), text (str), error (str | None)
    """
    if not SPEECH_AVAILABLE:
        return {
            "success": False,
            "text":    "",
            "error":   "SpeechRecognition library not installed. Run: pip install SpeechRecognition pyaudio",
        }

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise…")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Listening…")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)

        text = recognizer.recognize_google(audio)
        return {"success": True, "text": text, "error": None}

    except sr.WaitTimeoutError:
        return {"success": False, "text": "", "error": "No speech detected within timeout."}
    except sr.UnknownValueError:
        return {"success": False, "text": "", "error": "Could not understand audio. Please speak clearly."}
    except sr.RequestError as e:
        return {"success": False, "text": "", "error": f"Speech API error: {e}"}
    except Exception as e:
        return {"success": False, "text": "", "error": str(e)}


def is_voice_available() -> bool:
    """Check if microphone and speech recognition are available."""
    if not SPEECH_AVAILABLE:
        return False
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        if p.get_device_count() == 0:
            return False
        p.terminate()
        return True
    except Exception:
        return False
