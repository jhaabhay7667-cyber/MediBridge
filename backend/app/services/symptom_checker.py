
import json
import os
import re

import httpx


EMERGENCY_PHRASES = [
    "difficulty breathing",
    "cannot breathe",
    "can't breathe",
    "severe chest pain",
    "chest pressure",
    "unconscious",
    "not responding",
    "severe bleeding",
    "heavy bleeding",
    "face drooping",
    "slurred speech",
    "sudden weakness",
    "seizure",
    "severe allergic reaction",
    "throat swelling",
    "overdose",
    "suicide attempt",
    "self harm",
    "severe burn"
]


def detect_emergency(symptoms: str) -> bool:
    text = symptoms.lower()
    return any(phrase in text for phrase in EMERGENCY_PHRASES)


def emergency_result(language: str) -> dict:
    return {
        "urgency": "EMERGENCY",
        "summary": (
            "The symptoms entered may indicate a medical emergency. "
            "Immediate medical assessment is important."
        ),
        "possible_explanations": [],
        "self_care": [],
        "warning_signs": [
            "Do not delay seeking emergency medical help."
        ],
        "recommended_action": (
            "Call India's emergency number 112 now or go to the "
            "nearest emergency department. Do not drive yourself "
            "if you are seriously unwell."
        ),
        "disclaimer": (
            "This is a safety alert, not a diagnosis. "
            "The symptom checker cannot assess your condition reliably."
        )
    }


async def analyze_symptoms(
    symptoms: str,
    age: int | None,
    duration: str,
    severity: int,
    language: str
) -> dict:

    if detect_emergency(symptoms):
        return emergency_result(language)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    ).strip()

    prompt = f"""
You are a cautious health information assistant.

Analyze the user's symptom description for general educational
information only. You are NOT a doctor.

Return ONLY valid JSON. Do not use Markdown fences.

Required JSON structure:
{{
  "urgency": "LOW | MODERATE | HIGH | EMERGENCY",
  "summary": "Simple explanation in the requested language",
  "possible_explanations": ["Non-diagnostic possibilities"],
  "self_care": ["Low-risk general suggestions"],
  "warning_signs": ["Signs that require medical attention"],
  "recommended_action": "What the user should do next",
  "disclaimer": "This is not a medical diagnosis"
}}

Rules:
- Never claim a confirmed diagnosis.
- Never prescribe medicines or provide medicine dosages.
- Never invent medical history, test results, or symptoms.
- Do not falsely reassure the user.
- If symptoms suggest possible serious illness, choose HIGH or EMERGENCY.
- If uncertain, recommend professional medical assessment.
- Do not recommend delaying emergency care.
- Use short, understandable sentences.
- Respond in this language: {language}

User information:
Age: {age if age is not None else "Not provided"}
Duration: {duration or "Not provided"}
Severity (1-10): {severity}/10
Symptoms: {symptoms}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                json=payload
            )

        response.raise_for_status()
        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)

    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "The symptom analysis service is temporarily unavailable."
        ) from exc

    allowed_urgency = {
        "LOW", "MODERATE", "HIGH", "EMERGENCY"
    }

    urgency = str(result.get("urgency", "HIGH")).upper()

    if urgency not in allowed_urgency:
        urgency = "HIGH"

    def safe_list(value):
        if not isinstance(value, list):
            return []
        return [
            str(item)[:500]
            for item in value[:10]
            if isinstance(item, (str, int, float))
        ]

    return {
        "urgency": urgency,
        "summary": str(result.get("summary", ""))[:2000],
        "possible_explanations": safe_list(
            result.get("possible_explanations")
        ),
        "self_care": safe_list(result.get("self_care")),
        "warning_signs": safe_list(
            result.get("warning_signs")
        ),
        "recommended_action": str(
            result.get("recommended_action", "")
        )[:2000],
        "disclaimer": (
            "AI-generated health information only. "
            "This is not a medical diagnosis or a substitute "
            "for professional medical advice."
        )
    }
