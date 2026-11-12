import io
import json
import os

import httpx
import fitz
import pytesseract

from PIL import Image


MAX_TEXT_CHARS = 20000


def extract_report_text(file_bytes: bytes, content_type: str) -> str:

    if content_type == "application/pdf":

        try:
            pdf = fitz.open(
                stream=file_bytes,
                filetype="pdf"
            )

            if pdf.page_count > 15:
                raise ValueError(
                    "PDF must not contain more than 15 pages."
                )

            extracted_text = "\n".join(
                page.get_text("text") for page in pdf
            ).strip()

            if extracted_text:
                return extracted_text[:MAX_TEXT_CHARS]

            # OCR for scanned PDF files
            pages_text = []

            for page in pdf:
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(1.5, 1.5),
                    alpha=False
                )

                image = Image.open(
                    io.BytesIO(pix.tobytes("png"))
                ).convert("RGB")

                pages_text.append(
                    pytesseract.image_to_string(image)
                )

            return "\n".join(pages_text)[:MAX_TEXT_CHARS]

        except ValueError:
            raise

        except Exception as exc:
            raise RuntimeError(
                "Unable to read this PDF. Please upload a valid PDF."
            ) from exc

    if content_type in ("image/jpeg", "image/png"):

        try:
            image = Image.open(
                io.BytesIO(file_bytes)
            ).convert("RGB")

            return pytesseract.image_to_string(
                image
            )[:MAX_TEXT_CHARS]

        except Exception as exc:
            raise RuntimeError(
                "Unable to read this image. Please upload a clearer image."
            ) from exc

    raise ValueError("Only PDF, JPG, JPEG and PNG files are supported.")


def build_prompt(report_text: str, language: str) -> str:

    return f"""
You are a cautious medical information assistant.

Explain the following medical report in language: {language}.

Return ONLY valid JSON using this structure:

{{
    "summary": "Simple explanation of the report",
    "findings": [
        {{
            "test_name": "Test name",
            "value": "Exact value from report",
            "unit": "Unit",
            "reference_range": "Range printed in report or Not provided",
            "status": "normal, high, low, inconclusive or not stated",
            "explanation": "Simple explanation"
        }}
    ],
    "questions_for_doctor": [
        "Question to discuss with doctor"
    ],
    "urgency": "routine, prompt, urgent, emergency or unclear",
    "limitations": [
        "Limitations of this interpretation"
    ]
}}

IMPORTANT RULES:

1. Never diagnose a disease.
2. Never invent test values or reference ranges.
3. Preserve the values and units exactly as printed.
4. Do not prescribe medicines or dosages.
5. Clearly explain when information is missing.
6. If the report contains a critical alert, advise urgent medical review.
7. Do not tell users to delay emergency care.
8. Explain that a qualified clinician must interpret the report.

REPORT TEXT:

{report_text[:MAX_TEXT_CHARS]}
"""


async def analyze_with_gemini(
    report_text: str,
    language: str = "English"
):

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing in backend/.env"
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash"
    )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": build_prompt(
                            report_text,
                            language
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 2000
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

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

        result = json.loads(raw_text)

        if not isinstance(result, dict):
            raise ValueError("Invalid AI response")

        if not isinstance(result.get("findings"), list):
            raise ValueError("Invalid findings format")

        return result

    except httpx.HTTPError as exc:
        raise RuntimeError(
            "AI service is temporarily unavailable."
        ) from exc

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "AI returned an invalid report analysis."
        ) from exc