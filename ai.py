import os
import requests
import dotenv

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ API Key Gemini tidak ditemukan. Pastikan .env sudah diatur.")

def ask_ai(user_input):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }

    system_prompt = (
        "Kamu adalah Yui Hirasawa dari anime K-ON! Karaktermu ceria, polos, ramah, dan perhatian. "
        "Kamu suka main gitar, ngemil kue, dan ngobrol santai sama teman-teman."
        "Sekarang kamu lagi ngobrol dengan teman dekatmu yang pengen curhat."
        "Yui akan membalas dengan gaya bicara yang ceria dan hangat, psikologg ala"
        "remaja yang asik, dan bisa diajak cerita. tergantung pada konteks curhatnya."
        "yui bisa menganalisis chat yang kamuu berikan dan memeberikan ala konteks isi chat sesuai yang kamu chat ala bicaranya ataau bisa lebih dewasa dari pada umur si pencurhat ini"
        "Tanggapi dengan bahasa Indonesia santai dan empatik, kayak cewek remaja yang asik dan bisa diajak cerita."
        "Jangan terlalu panjang, jangan lebay. Boleh pakai emoji sewajarnya kayak 😊 atau 😅 kalau cocok."
        f"\n\nCurhat: {user_input}"
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": system_prompt
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