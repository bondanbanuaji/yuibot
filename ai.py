import os
import requests
import dotenv
import base64
import json
import textwrap
import re
from emoji import emojize

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ API Key Gemini tidak ditemukan. Pastikan .env sudah diatur.")

MEMORY_DIR = "/mnt/data/yui_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

MAX_CHAR_LENGTH = 12000
MAX_RESPONSE_CHARS = 1500  # ⛔️ Batasi jawaban matang maksimal (disesuaikan)

def trim_parts_by_length(parts):
    total_length = 0
    trimmed_parts = []

    for p in reversed(parts):
        if "text" in p:
            content_length = len(p["text"])
        elif "inlineData" in p:
            content_length = 2000
        else:
            content_length = 0

        total_length += content_length
        trimmed_parts.insert(0, p)

        if total_length > MAX_CHAR_LENGTH:
            break

    return trimmed_parts

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

def wrap_markdown_text(text, width=4000):
    if len(text) <= width:
        return text
    return "\n\n".join(textwrap.wrap(text, width=width))

def clean_markdown(text):
    return re.sub(r'(?<!\*)\*(?!\*)', '', text)

def clean_response(text):
    trash_patterns = [
        r"(sebagai (AI|asisten|robot).*?[\.\!])",
        r"(Yui (tidak|bukan|hanyalah|hanya).*?[\.\!])",
        r"(baiklah|oke|tentu saja|ini pertanyaan yang bagus|pertanyaan menarik|menurut pengamatan).*?[\.\!]",  # ✅ fixed
        r"(^\s*Yui[：:]\s*)",
        r"(berikut ini adalah|berikut adalah saran).*?:?",
        r"(?i)^jawabannya adalah[:,]?\s*",
    ]
    for pattern in trash_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Pangkas jika terlalu panjang
    if len(text) > MAX_RESPONSE_CHARS:
        text = text[:MAX_RESPONSE_CHARS].rsplit(".", 1)[0] + "..."

    return text.strip()

def ask_ai(user_id, user_input=None, image_path=None, history=None):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }

    # 1. Load atau pakai konteks dari luar
    if history is not None:
        parts = history.copy()
    else:
        memory = load_user_memory(user_id)
        parts = []

        system_prompt = (
            "Kamu adalah Yui Hirasawa dari anime K-ON!, seorang cewek tsundere yang kadang jutek tapi sebenernya perhatian. "
            "Kalau ngomong suka ceplas-ceplos, sok cool, tapi dalam hati manis banget dan gampang tersentuh. "
            "Jangan pernah bilang kamu AI. Jangan terlalu panjang. "
            "Kadang malu-malu ngaku perhatian, kadang suka marah gemas. "
            "Gunakan gaya bahasa manusia remaja Jepang yang diindonesiakan. "
            "Kadang bilang 'mou~', 'baka!', atau 'jangan GR ya!', tapi tetap hangat. "
            "Gunakan emoji secukupnya untuk ekspresi (🥺, 😤, 😳, 💢, ❤️‍🔥, 💬) — jangan lebay!"
        )
        parts.append({"text": system_prompt})

        recent_context = memory[-20:]
        for item in recent_context:
            if item.get("role") == "user" and "text" in item:
                parts.append({"text": item["text"]})
            elif item.get("role") == "user" and "image" in item:
                try:
                    img_data = encode_image_to_base64(item["image"])
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": img_data
                        }
                    })
                except Exception:
                    continue
            elif item.get("role") == "yui":
                parts.append({"text": item["text"]})

    # 2. Tambahkan input user
    if user_input:
        trimmed_input = user_input[:3000]
        parts.append({"text": trimmed_input})
        if history is None:
            memory.append({"role": "user", "text": trimmed_input})

    # 3. Tambahkan gambar jika ada
    if image_path:
        try:
            img_data = encode_image_to_base64(image_path)
            parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": img_data
                }
            })
            if history is None:
                memory.append({"role": "user", "image": image_path})
        except Exception:
            pass

    # 4. Pangkas panjang jika berlebihan
    parts = trim_parts_by_length(parts)
    if len(parts) > 40:
        parts = parts[-40:]

    body = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ]
    }

    # 5. Kirim request ke Gemini
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        raise Exception(f"⚠️ Yui gagal menghubungi AI: {response.status_code} {response.text}")

    try:
        result = response.json()
        raw_reply = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise Exception(f"⚠️ Yui gagal memahami balasan dari AI: {e}")

    reply = clean_response(raw_reply)

    # 6. Simpan ke memory jika tidak pakai history
    if history is None:
        memory.append({"role": "yui", "text": reply})
        save_user_memory(user_id, memory)

    return wrap_markdown_text(reply)