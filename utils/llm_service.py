"""
utils/llm_service.py
---------------------
Groq API integration (llama3-70b-8192 or configured model).
Handles interview question generation, answer evaluation, and learning roadmaps.
Falls back to a deterministic stub if Groq is unavailable or key is missing.
"""

import json
import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Groq configuration ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_groq_client = None


def _get_groq_client():
    """Lazy-initialise and return the Groq client."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file.\n"
            "Get a free key at https://console.groq.com"
        )
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
        return _groq_client
    except ImportError:
        raise RuntimeError(
            "groq package not installed. Run: pip install groq"
        )


def _call_groq(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """
    Send a chat completion request to Groq and return the assistant text.
    Raises RuntimeError if Groq is unreachable or key is missing.
    """
    client = _get_groq_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=2048,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"Groq API error: {exc}")


def is_groq_available() -> bool:
    """Check whether the Groq client can be initialised (key is present)."""
    try:
        _get_groq_client()
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Interview question generation
# ──────────────────────────────────────────────────────────────────────────────

_QUESTION_SYSTEM = (
    "You are an expert technical interviewer. "
    "Generate realistic, role-specific interview questions. "
    "Return ONLY valid JSON — no markdown, no code fences, no extra text."
)


def generate_interview_questions(
    job_role: str,
    skills: list[str] | None = None,
    num_technical: int = 5,
    num_hr: int = 3,
) -> dict[str, list[str]]:
    """
    Generate technical + HR interview questions for a job role using Groq.

    Returns
    -------
    dict with keys "technical" and "hr", each a list of question strings.
    """
    skills_str = ", ".join(skills[:15]) if skills else "general programming"
    prompt = (
        f"Generate exactly {num_technical} technical interview questions and "
        f"{num_hr} HR/behavioural interview questions for the role of "
        f"'{job_role}'. The candidate's key skills include: {skills_str}.\n\n"
        "Return a JSON object with two keys:\n"
        "  - \"technical\": list of technical question strings\n"
        "  - \"hr\": list of HR/behavioural question strings\n"
        "Example: {\"technical\": [\"Q1\", \"Q2\"], \"hr\": [\"Q1\"]}"
    )

    try:
        raw = _call_groq(prompt, _QUESTION_SYSTEM, temperature=0.8)
        # Strip markdown code fences if model wraps JSON
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "technical": data.get("technical", [])[:num_technical],
                "hr":        data.get("hr", [])[:num_hr],
            }
    except Exception as exc:
        logger.warning("Groq question generation failed (%s) – using fallback.", exc)

    # Fallback: return sensible generic questions
    return {
        "technical": [
            f"Explain a core concept of {job_role} that you use regularly.",
            f"How do you ensure code quality and maintainability in a {job_role} project?",
            "Describe your approach to debugging a complex production issue.",
            "How do you stay current with new technologies and best practices?",
            f"Walk me through a challenging {job_role} project from start to finish.",
        ][:num_technical],
        "hr": [
            "Tell me about yourself and what drives your passion for this field.",
            "Describe a time you had to meet a tight deadline under pressure.",
            "How do you handle disagreements within a team?",
        ][:num_hr],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Answer evaluation
# ──────────────────────────────────────────────────────────────────────────────

_EVAL_SYSTEM = (
    "You are an expert technical interview evaluator. "
    "Evaluate the candidate's answer objectively and constructively. "
    "Return ONLY a valid JSON object (no markdown, no code fences) with these exact keys: "
    "relevance_score (0-10), clarity_score (0-10), technical_score (0-10), "
    "communication_score (0-10), overall_score (0-10), "
    "feedback (string, 2-3 sentences), improvement_tips (list of 2-3 strings)."
)


def evaluate_answer(
    question: str,
    answer: str,
    job_role: str = "",
) -> dict:
    """
    Evaluate a single interview answer using Groq.

    Returns
    -------
    dict with scores and feedback.
    """
    if not answer or len(answer.strip()) < 5:
        return _empty_evaluation("Answer is too short to evaluate meaningfully.")

    prompt = (
        f"Job Role: {job_role or 'General'}\n"
        f"Interview Question: {question}\n"
        f"Candidate's Answer: {answer}\n\n"
        "Evaluate this answer. Return a JSON object as instructed with all required keys."
    )

    try:
        raw = _call_groq(prompt, _EVAL_SYSTEM, temperature=0.4)
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            data = json.loads(json_match.group())
            # Clamp all scores to 0-10
            for key in ("relevance_score", "clarity_score",
                        "technical_score", "communication_score", "overall_score"):
                val = data.get(key, 5)
                data[key] = max(0.0, min(10.0, float(val)))
            if "improvement_tips" not in data:
                data["improvement_tips"] = []
            if "feedback" not in data:
                data["feedback"] = "Good effort. Keep practising."
            return data
    except Exception as exc:
        logger.warning("Groq evaluation failed (%s) – using heuristic.", exc)

    return _heuristic_evaluation(answer)


def _empty_evaluation(reason: str) -> dict:
    return {
        "relevance_score": 0, "clarity_score": 0,
        "technical_score": 0, "communication_score": 0,
        "overall_score": 0,
        "feedback": reason,
        "improvement_tips": ["Please provide a more detailed answer."],
    }


def _heuristic_evaluation(answer: str) -> dict:
    """Simple heuristic fallback when Groq is unavailable."""
    words = len(answer.split())
    base = min(10.0, words / 15.0)   # ~150 words → 10
    return {
        "relevance_score":     round(base * 0.9,  1),
        "clarity_score":       round(base * 0.85, 1),
        "technical_score":     round(base * 0.80, 1),
        "communication_score": round(base * 0.90, 1),
        "overall_score":       round(base * 0.86, 1),
        "feedback": (
            "AI evaluation unavailable – heuristic score based on answer length. "
            "Ensure your GROQ_API_KEY is set in the .env file."
        ),
        "improvement_tips": [
            "Provide specific examples and quantifiable outcomes.",
            "Structure your answer using the STAR method (Situation, Task, Action, Result).",
            "Ensure technical terms are explained clearly and concisely.",
        ],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Learning roadmap generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_learning_roadmap(
    missing_skills: list[str],
    job_role: str,
    user_skills: list[str] | None = None,
) -> dict:
    """
    Generate a personalised learning roadmap using Groq.
    Returns a dict with phase-based roadmap and resource suggestions.
    """
    if not missing_skills:
        return {"message": "You already have all the required skills!", "phases": []}

    skills_str = ", ".join(missing_skills[:15])
    user_str   = ", ".join((user_skills or [])[:10])
    prompt = (
        f"I want to become a {job_role}.\n"
        f"My current skills: {user_str or 'beginner level'}.\n"
        f"Skills I need to learn: {skills_str}.\n\n"
        "Create a structured 3-phase learning roadmap. "
        "For each phase include: 'phase' (name string), 'duration' (e.g. '4 weeks'), "
        "'skills' (list of skill strings), 'resources' (list of free online resource URLs). "
        "Return ONLY a valid JSON object with key 'phases' containing the list of phase objects. "
        "No markdown, no code fences."
    )
    try:
        raw = _call_groq(prompt, "You are an expert career coach and educator.", temperature=0.6)
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            return json.loads(json_match.group())
    except Exception as exc:
        logger.warning("Roadmap generation failed (%s) – using fallback.", exc)

    # Deterministic fallback
    phases = []
    chunks = [missing_skills[i:i + 3] for i in range(0, len(missing_skills), 3)]
    phase_names = ["Foundation", "Intermediate", "Advanced"]
    for i, chunk in enumerate(chunks[:3], 1):
        query = "+".join(chunk[:1])
        phases.append({
            "phase":    f"Phase {i} – {phase_names[i - 1]}",
            "duration": f"{4 * i} weeks",
            "skills":   chunk,
            "resources": [
                f"https://www.coursera.org/search?query={query}",
                f"https://www.youtube.com/results?search_query={query}+tutorial",
                "https://roadmap.sh",
                "https://www.freecodecamp.org",
            ],
        })
    return {"phases": phases}
