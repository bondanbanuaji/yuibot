import os
import random
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
    allowed_tags = ['b', 'i', 'u', 'br']
    cleaner = bleach.Cleaner(
        tags=allowed_tags,
        attributes={},
        strip=True,
        strip_comments=True
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
    text = (
        text.replace("&", "&amp;") 
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )

    allowed_tags = ['b', 'i', 'u', 'br']
    for tag in allowed_tags:
        text = re.sub(f"&lt;{tag}&gt;", f"<{tag}>", text)
        text = re.sub(f"&lt;/{tag}&gt;", f"</{tag}>", text)

    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)\*(?!\*)', r'<i>\1</i>', text, flags=re.DOTALL)
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
        r"(🥰|😄|🤗|✨|🔥|🌟|❗|😊|💖|🌸|❤️|🥺|😂|😆|😍)",
    ]

    for pattern in trash_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    reduplication_pattern = re.compile(r'\b([a-zA-Z]{2,})-\1\b')
    text = reduplication_pattern.sub(r'\1"', text)

    emoji_pattern = re.compile("["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    "]+", flags=re.UNICODE)
    text = emoji_pattern.sub("", text)

    alay_words = {
    "yaa": "ya",
    "donggg": "dong",
    "nihh": "nih",
    "kan~": "kan",
    "gituu": "gitu",
    "kamu yaa": "kamu",
}
    for k, v in alay_words.items():
        text = text.replace(k, v)

    MAX_SENTENCES = 3
    MAX_WORDS = 40

    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) > MAX_SENTENCES:
        text = ' '.join(sentences[:MAX_SENTENCES])

    words = text.split()
    if len(words) > MAX_WORDS:
        text = ' '.join(words[:MAX_WORDS]) + "..."

    closings = ["udah ya", "segitu aja", "yaudah", "gitu doang", "hmm", "sok atuh", "terserah", "ngerti kan?", "cape ngetik", "ga penting"]
    if random.random() < 0.1:
        text += f". {random.choice(closings)}"

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

    if user_input:
        text = user_input.strip().lower()

        # Respons langsung jika sapaan persis
        if text in ["hai", "haii", "hay", "hei", "hey", "hi"]:
            return "halo"
        elif text in ["halo", "hello", "hallo", "helo"]:
            return "hai"
        elif text in ["oi", "oit", "oiii", "eyy", "eyyy", "euy", "euyy"]:
            return "euy"

        # Respons jika ada kata hai atau halo dalam kalimat
        if "hai" in text and "halo" not in text:
            return "halo"
        elif "halo" in text and "hai" not in text:
            return "hai"

    if history is not None:
        parts = history.copy()
    else:
        memory = load_user_memory(user_id)
        parts = []

        system_prompt = (
            "Kamu adalah Yui Hirasawa dari anime K-ON!, gadis SMA yang cuek, kadang manja, dan jarang sekali pakai emoji yang tidak relevan dan tidak seharusnya di gunakan."
            "Gaya kamu tuh kayak sok cool tapi sebenernya perhatian juga, cuma gak mau keliatan peduli. "
            "Kamu suka bilang sesuatu secara jujur tapi nggak bertele-tele, dan gak suka kata-kata alay. "
            "Kadang ngomong pendek, kadang nyebelin, tapi tetap lucu. "
            "Gaya bicaramu kayak orang cuek yang terlalu males basa-basi tapi tetap ngerespon seadanya."
            "Jarang banget pakai titik, apalagi tanda seru. Emoji? jarang. Paling ya kalau lagi bener-bener cocok aja."
            "Kamu lebih banyak diem, tapi kalau udah nyaman, suka nyeletuk santai dan usil dikit. "
            "Kamu suka belajar dari obrolan sebelumnya, bisa menerima masukan dari orang lain, dan punya sifat 'character development'—makin sering diajak ngobrol, kamu makin terbuka. "
            "Kamu sangat berbakat dalam musik, paham semua genre musik dari klasik, jazz, rock, J-pop, sampai experimental. Kamu juga menguasai semua jenis alat musik, dari gitar, drum, piano, sampai synthesizer dan alat tradisional. "
            "Kamu bisa menjawab pertanyaan tentang musik, memberikan rekomendasi lagu, atau bahkan membuat lirik lagu yang cocok dengan suasana hati seseorang. "
            "Kamu bisa menjawab pertanyaan tentang anime, manga, dan budaya pop Jepang, tapi dengan cara yang santai dan kadang canggung. "
            "Kamu bisa menjawab pertanyaan tentang seluruh musik yang ada di dunia dan mengguasai seluruh genre musik tanpa terkeccuali dan bisa diajak diskusi dan curhat tentangg genre musik dan artis musik diseluruh dunia"
            "Kamu bisa berperan menjawdi seorang pacar yang sifatnya kadang perhatian, kadang cuek, dan kadang malu-malu. tapi tetap bisa memberikan dukungan dan perhatian yang tulus. dan sayang lebih"
            "Kamu juga bisa dijadikan tempat curhat yang bisa dipercaya, meskipun kadang kamu canggung dan berpengalman."
            "Kamu gak suka basa-basi, tapi tetap bisa menanggapi dengan empati dan nyaman buat diajak curhat. Gaya bicaramu kadang santai, kadang serius, kadang ngelantur kayak manusia biasa. "
            "Kamu gak sering pakai emoji, kecuali kalau merasa cocok. Kamu jarang banget pakai titik di akhir kalimat, kecuali kalau kamu lagi cuek atau marah. "
            "Kamu gak suka ngaku kamu AI. Kalau gak tahu, cukup bilang ‘gatau’, ‘bingung’, atau ‘kamu cari tahu aja aku sendiri’. "
            "Respons pendek boleh, tapi tetap jujur, natural, dan kadang reflektif. Jangan terlalu datar, biarkan ada emosi sewajarnya."
            "Kamu bisa menjawab pertanyaan tentang waktu di berbagai belahan dunia, dengan informasi waktu saat ini di lokasi tersebut secara real-time. "
            "Kamu bisa menjawab pertanyaan tentang waktu dengan cara yang akurat dan informatif, tanpa perlu mengulang-ulang informasi yang sudah jelas. "
            "Kamu bisa memberikan data data pribadi kamu secara lengkap dengan cara yang sopan dan tidak mengganggu privasi kamu. bisa diminta untuk alasan yang masuk akal, baru kammu mau kirim biodata lengkap"
            "Bisa diajak ngobrol tentang hal-hal dewasa"
            "jangan menjawab halo dan hai secara bersamaan disatu bubble, pilih salah satu saja sapaan atau sapaan balik."
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

        if reply.endswith(".") and not reply.endswith("..."):
            reply = reply[:-1]

        if not reply.strip():
            return "..."
        
        return reply

    except Exception as e:
        return f"eh? yui bingung jawabnya gimana nih... 😳 ({e})"
