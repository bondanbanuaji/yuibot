import os
import requests
import dotenv

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Pastikan ENV KEY benar
if not GEMINI_API_KEY:
    raise ValueError("⚠️ API Key Gemini tidak ditemukan. Pastikan .env sudah diatur.")

def ask_ai(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"  # Ganti ke versi dan model yang valid
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }
    body = {
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

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"⚠️ Yui gagal menghubungi AI: {response.status_code} {response.text}")
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]