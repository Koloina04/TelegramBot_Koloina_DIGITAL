import os
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def generate_text(prompt):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY n'est pas défini.")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(
        GEMINI_URL,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(
            f"Gemini HTTP {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Réponse Gemini inattendue : {data}")


if __name__ == "__main__":
    result = generate_text(
        "Réponds uniquement : Gemini est correctement connecté au bot."
    )
    print(result)
