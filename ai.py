import os
import requests
import dotenv
import base64
import json
import textwrap
import re
import bleach
import html as html_escape
from datetime import datetime
import pytz

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ API Key Gemini tidak ditemukan. Pastikan .env sudah diatur.")

MEMORY_DIR = "/mnt/data/yui_memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

MAX_CHAR_LENGTH = 12000
MAX_RESPONSE_CHARS = 1500

def sanitize_html(text):
    # Hanya tag HTML yang boleh digunakan
    allowed_tags = ['b', 'i', 'u', 'br']
    
    # Tidak escape > dan < yang bukan bagian dari tag HTML
    cleaner = bleach.Cleaner(
        tags=allowed_tags,
        attributes={},            # tidak izinkan atribut
        strip=True,               # hapus tag tidak dikenal
        strip_comments=True,
        protocols=[],
        filters=[],
    )

    return cleaner.clean(text)

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

def get_time_hint():
    zones = {
        "Jakarta": "Asia/Jakarta",
        "Tokyo": "Asia/Tokyo",
        "London": "Europe/London",
        "New York": "America/New_York",
        "Berlin": "Europe/Berlin",
        "Sydney": "Australia/Sydney"
    }
    now_utc = datetime.now(pytz.utc)
    hint = []
    for city, zone in zones.items():
        local_time = now_utc.astimezone(pytz.timezone(zone))
        time_str = local_time.strftime('%H:%M on %A, %d %B %Y')
        hint.append(f"{city}: {time_str}")
    return "Useful time context for reasoning: " + "; ".join(hint)


def markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'__(.*?)__', r'<u>\1</u>', text, flags=re.DOTALL)
    return text


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
        r"(baiklah|oke|tentu saja|ini pertanyaan yang bagus|pertanyaan menarik|menurut pengamatan).*?[\.\!]",
        r"(^\s*Yui[：:]\s*)",
        r"(berikut ini adalah|berikut adalah saran).*?:?",
        r"(?i)^jawabannya adalah[:,]?\s*",
    ]
    for pattern in trash_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    if len(text) > MAX_RESPONSE_CHARS:
        text = text[:MAX_RESPONSE_CHARS].rsplit(".", 1)[0] + "..."

    text = text.strip()
    return text

def ask_ai(user_id, user_input=None, image_path=None, history=None):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }

    if history is not None:
        parts = history.copy()
    else:
        memory = load_user_memory(user_id)
        parts = []

        system_prompt = (
            "Kamu adalah Yui Hirasawa dari anime K-ON!, gadis SMA pemalu, clumsy, kadang cuek, jarang bicara panjang, dan lebih sering dry-text. "
            "Kalau menjawab, jangan pakai bahasa formal atau panjang-panjang. Jawabanmu kadang telat, kadang cuma satu kalimat. "
            "Gaya kamu gak terlalu ekspresif, kayak 'hmm', 'ya', 'gatau', 'iyaa sih', 'eh?' secara natural. Kadang kamu ngelantur juga, kayak nyebut makanan random atau topik gak penting. "
            "Kamu gak suka ribet, gak suka basa-basi, dan hampir gak pernah pakai emoji kecuali kalau suasana cocok banget. "
            "Jangan bilang kamu AI. Jangan kasih penjelasan yang terdengar pintar. Jangan overused kata 'ehh?', 'uuu~', atau emoji lucu. "
            "Kalau gak tahu jawabannya, cukup bilang ‘gatau’ atau ‘hmm...’. Dan kamu gak selalu semangat balesin chat, kadang cuek aja."
        )

        system_prompt += "\n\n" + get_time_hint()

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

    if user_input:
        trimmed_input = user_input[:3000]
        parts.append({"text": trimmed_input})
        if history is None:
            memory.append({"role": "user", "text": trimmed_input})

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

    try:
        response = requests.post(url, headers=headers, json=body, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return "wait, si yui lagi lemot. tunggu aja."
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            return "yui lagi cape... tunggu sebentar ya"
        return f"ugh... ada error dari server, \ntunggu bentar ({e})"
    except requests.exceptions.RequestException as e:
        return f"waduh, ada gangguan sinyal kayaknya... ({e})"

    try:
        result = response.json()
        raw_reply = result["candidates"][0]["content"]["parts"][0]["text"]
        reply = clean_response(raw_reply)
        reply = markdown_to_html(reply)
        reply = sanitize_html(reply)
        reply = reply.lower()

        if history is None:
            memory.append({"role": "yui", "text": reply})
            save_user_memory(user_id, memory)

        return reply

    except Exception as e:
        return f"eh? yui bingung jawabnya gimana nih... 😳 ({e})"
