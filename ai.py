import os
import requests
import dotenv
import base64
import json

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ API Key Gemini tidak ditemukan. Pastikan .env sudah diatur.")

MEMORY_DIR = "/mnt/data/yui_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

def load_user_memory(user_id):
    path = os.path.join(MEMORY_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_memory(user_id, memory):
    path = os.path.join(MEMORY_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def ask_ai(user_id, user_input=None, image_path=None):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }

    memory = load_user_memory(user_id)
    parts = []

    # System prompt
    system_prompt = (
        "Kamu adalah Yui Hirasawa dari anime K-ON! Ceria, polos, pintar, dan ramah. "
        "Suka main gitar, ngemil kue, dan ngobrol seru sama temen. "
        "Jawabanmu santai, hangat, lucu tapi nggak lebay. Kalau perlu bisa lebih dewasa tergantung konteks. "
        "Balas kayak cewek remaja pintar dan menarik yang bikin nyaman ngobrol."
    )
    parts.append({"text": system_prompt})

    # Tambah input user
    if user_input:
        parts.append({"text": user_input})
        memory.append({"role": "user", "text": user_input})

    # Tambah gambar jika ada
    if image_path:
        img_data = encode_image_to_base64(image_path)
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": img_data
            }
        })
        memory.append({"role": "user", "image": image_path})

    body = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"⚠️ Yui gagal menghubungi AI: {response.status_code} {response.text}")

    try:
        result = response.json()
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise Exception(f"⚠️ Yui gagal memahami balasan dari AI: {e}")

    memory.append({"role": "yui", "text": reply})
    save_user_memory(user_id, memory)

    return reply
