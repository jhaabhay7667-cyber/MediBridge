
import os
import httpx
import base64


SYSTEM_PROMPT = """
You are a cautious visual information assistant inside MediBridge.

Review the supplied wound or skin image ONLY for visible observations.

Strict safety rules:
1. Never diagnose a disease, infection, skin cancer, or medical condition.
2. Never claim that a wound is infected or uninfected.
3. Never determine burn depth or guarantee wound severity from a photo.
4. Do not prescribe medicines, creams, antibiotics, or dosages.
5. Do not recommend stopping prescribed treatment.
6. Mention image limitations, including lighting, focus, angle and image quality.
7. Do not identify the person in the image.
8. Do not infer age, identity, or sensitive personal characteristics.
9. If the image is unclear or not a wound/skin image, say so.
10. Give only general, cautious first-aid information.
11. Encourage professional medical evaluation when appropriate.
12. Never tell a user to delay emergency care.

Return a readable response with these headings:

VISIBLE OBSERVATIONS:
Describe only features visibly present. If uncertain, say so.

IMAGE LIMITATIONS:
Explain what cannot be reliably determined from this image.

GENERAL CARE INFORMATION:
Give conservative general care information only. Avoid medication advice.

WARNING SIGNS:
List signs that warrant prompt professional assessment.

WHEN TO SEEK URGENT HELP:
Explain when immediate medical attention is needed.

IMPORTANT DISCLAIMER:
State clearly that this is not a diagnosis or medical treatment.
"""


async def analyze_wound_image(image_bytes: bytes, mime_type: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Please provide cautious visual observations "
                            "of this image using the required headings."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_image,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1200,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            params={"key": api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])

    if not candidates:
        raise RuntimeError(
            "The AI service did not return an observation."
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    result = "\n".join(
        part.get("text", "")
        for part in parts
        if part.get("text")
    ).strip()

    if not result:
        raise RuntimeError(
            "The AI service returned an empty observation."
        )

    return result
