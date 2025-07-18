import os
import logging
import asyncio
import random
import tempfile
from telegram.helpers import escape_markdown
from telegram.constants import ChatAction, ParseMode
from ai import ask_ai
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from datetime import datetime
import pytz

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

user_states = {}
user_contexts = {}

async def musikinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    musik_tip = random.choice([
        "kamu tau nggak... tuning open d tuh cocok banget buat lagu galau akustik",
        "aku suka banget chord progressions jazz... kaya ii-V-I, bikin suasana adem",
        "dulu aku latihan metronome tiap malam... boring tapi ngaruh banget",
        "kalau pengen belajar drum digital, coba install hydrogen di linux... ringan dan powerful",
        "aku pernah ngeband genre math rock, capek tapi seru... kamu suka?",
        "kamu pernah coba mainin lagu klasik di piano rasanya kaya bener-bener nyatu sama musiknya",
        "Kamu bisa memberikan rekomendasi lagu-lagu indie yang lagi hits di kalangan anak muda",
        "Kamu hapal semua lagu dari band-band legendaris seperti The Beatles, Queen, Gun N Roses dan Nirvana",
        "Kamu expert di semua genre musik, dari klasik, jazz, rock, J-pop, sampai experimental",
        "Kamu bisa membuat lirik lagu yang cocok dengan suasana hati seseorang, apapun genre musiknya",
        "Kamu bisa menjawab pertanyaan tentang musik, memberikan rekomendasi lagu, atau bahkan membuat lirik lagu yang cocok dengan suasana hati seseorang",
        "Kamu bisa menjawab pertanyaan tentanggg efek gitar listrik, dari overdrive, distortion, sampai delay, reverb dan lain-lain",
        "Kamu bisa menjawab pertanyaan kalau ditanya tentang efek apa yang diggunakan pada suuatu lagu, dari efek gitar, bass, drum, sampai keyboard secara akurat dan benar",
        "Kamu juga bisa menjawab pertanyaan kalau ditanya detail dan kompleks settingan efek efek gitar, bass, drum, sampai keyboard secara akurat dan benar",
        "Kamu bisa menjawab pertanyaan seputar teknik bermain gitar seperti fingerstyle, strumming, tappingg, sweep picking, dan lain-lain",


    ])
    await update.message.reply_text(musik_tip, parse_mode=ParseMode.MARKDOWN)

async def send_long_message(update, text, parse_mode=ParseMode.HTML):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for paragraph in paragraphs:
            await update.message.reply_text(paragraph, parse_mode=parse_mode)
            await asyncio.sleep(1.6, 2.8)

    MAX_LENGTH = 3000

    if len(text) <= MAX_LENGTH:
        await update.message.reply_text(text, parse_mode=parse_mode)
    else:
        for i in range(0, len(text), MAX_LENGTH):
            chunk = text[i:i + MAX_LENGTH]
            await update.message.reply_text(chunk, parse_mode=parse_mode)

def is_time_query(text):
    kws = ["jam", "waktu", "what time", "waktu sekarang", "jam berapa"]
    return any(kw in text.lower() for kw in kws)

def get_world_times():
    zones = {
        "🇮🇩 Jakarta": "Asia/Jakarta",
        "🇯🇵 Tokyo": "Asia/Tokyo",
        "🇰🇷 Seoul": "Asia/Seoul",
        "🇨🇳 Beijing": "Asia/Shanghai",
        "🇸🇬 Singapore": "Asia/Singapore",
        "🇮🇳 New Delhi": "Asia/Kolkata",
        "🇦🇪 Dubai": "Asia/Dubai",
        "🇿🇦 Cape Town": "Africa/Johannesburg",
        "🇬🇧 London": "Europe/London",
        "🇩🇪 Berlin": "Europe/Berlin",
        "🇫🇷 Paris": "Europe/Paris",
        "🇧🇷 São Paulo": "America/Sao_Paulo",
        "🇺🇸 New York": "America/New_York",
        "🇺🇸 Los Angeles": "America/Los_Angeles",
        "🇲🇽 Mexico City": "America/Mexico_City",
        "🇦🇺 Sydney": "Australia/Sydney",
        "🇳🇿 Wellington": "Pacific/Auckland"
    }
    
    try:
        now_utc = datetime.now(pytz.utc)
        time_list = []
        
        for city, tz in zones.items():
            try:
                tz_obj = pytz.timezone(tz)
                local_time = now_utc.astimezone(tz_obj)
                time_str = local_time.strftime('%H:%M')
                date_str = local_time.strftime('%a, %d %b %Y')
                time_list.append(f"• {city}: {time_str} ({date_str})")
            except Exception as e:
                logging.error(f"Error processing timezone {tz}: {e}")
                continue
                
        return "🕒 Waktu Dunia:\n" + "\n".join(time_list)
        
    except Exception as e:
        logging.error(f"error getting world times: {e}")
        return "⚠️ maaf, yui lagi error cek waktu. coba lagi nanti ya..."

async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Jangan proses jika dalam mode stopped
    if user_states.get(user_id) == "stopped":
        return

    # Cek query waktu (kecuali dalam mode curhat)
    if (update.message.text and 
        user_states.get(user_id) != "curhat_ai" and 
        is_time_query(update.message.text)):
        
        await update.message.reply_chat_action(ChatAction.TYPING)
        times = get_world_times()
        await update.message.reply_text(
            times,
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=update.message.message_id
        )
        return

# ======= /start =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "active"
    user_contexts[user_id] = {"texts": [], "images": []}
    name = user.first_name if user else "teman baru"
    emotions = [
        "h-halo... aku nggak terlalu pandai mulai ngobrol sih 😳", 
        "hmm... kamu baik-baik aja kan? bukan urusanku sih, cuma nanya aja...", 
        "ehh... kamu dateng juga ya... yaudah, duduk sana dulu", 
        "aku di sini sih... walau agak malas balesin, tapi aku dengerin kok"
    ]


    await update.message.reply_animation(
        animation="https://media1.tenor.com/m/ohxROUA8aW0AAAAd/shy-cute.gif"
    )

    welcome_text = (
        f"{random.choice(emotions)}\n\n"
        f"nama aku... Yui... gitu aja.\n"
        "kalau mau cerita, ya cerita aja sih.\n"
        "aku dengerin kok... cuma ya... kadang males bales...\n"
        "_yaudah... coba aja chat._"
        "📌 oh iya cobain juga beberapa hal seru lainnya:\n"
        "  • /motivasi — buat semangat lagi\n"
        "  • /quotes — kata bijak hari ini\n"
        "  • /pantun — hiburan receh 😆\n"
        "  • /curhat — pas pengen cerita aja\n\n"
        "_Yuk mulai ngobrol, aku udah siap!_ 💬"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

# ======= /help =======
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *Butuh bantuan? Nih, panduannya:*\n\n"
        "Kamu bisa kirim pesan apapun dan Yui bakal jawab langsung.\n\n"
        "🔧 *Perintah yang bisa kamu pakai:*\n"
        "  ▪️ /start — Sapaan manis dari Yui + animasi lucu\n"
        "  ▪️ /help — Lihat daftar kemampuan Yui\n"
        "  ▪️ /stop — Mengakhiri percakapan\n"
        "  ▪️ /clearchat — Hapus semua pesan dari Yui\n\n"
        "  ▪️ /motivasi — Kata-kata penyemangat 🔥\n"
        "  ▪️ /quotes — Kutipan inspiratif 📖\n"
        "  ▪️ /pantun — Pantun lucu buat nyegerin kepala\n"
        "  ▪️ /curhat — Tempat cerita yang aman dan tenang 🫂\n\n"
        "Silakan coba, Yui tunggu yaa~ 🌷"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# ======= /motivasi =======
def generate_motivasi():
    motivasi = [
        "ya... semangat... gitu deh.",
        "hidup tuh... ya... gitu aja.",
        "cape? ya tidur lah.",
        "kadang... diem juga solusi.",
        "mikir tuh... bikin pusing.",
        "kalo nggak kuat, ya jangan maksain.",
        "aku juga... males sebenernya.",
        "kadang nugas... kadang ngelamun.",
        "teh anget... enak sih.",
        "mau makan roti... tapi males ngunyah.",
        "hmm... good luck... maybe.",
        "jangan tanya aku, aku juga bingung.",
        "ya jalanin aja... katanya gitu.",
        "...gatau juga sih.",
    ]
    return random.choice(motivasi)


async def motivasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_states.get(update.effective_user.id) != "active":
        return
    kata = random.choice(motivasi)
    await update.message.reply_text(kata, parse_mode=ParseMode.MARKDOWN)

# ======= /quotes =======
quotes_list = [
    "“Hidup itu 10% apa yang terjadi padamu dan 90% bagaimana kamu meresponnya.” – Charles R. Swindoll",
    "“Jangan takut gagal. Takutlah untuk tidak mencoba.” – Roy T. Bennett",
    "“Satu-satunya batasan adalah yang kamu tetapkan sendiri.”",
    "“Percaya pada diri sendiri meski orang lain belum tentu percaya.”",
    "“Kerja keras ngalahin bakat, apalagi kalau bakatnya tidur.”"
]

async def quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_states.get(update.effective_user.id) != "active":
        return
    kutipan = random.choice(quotes_list)
    await update.message.reply_text(f"📖 *Quotes buat kamu hari ini:*\n\n_{kutipan}_", parse_mode=ParseMode.MARKDOWN)

# ======= /pantun =======
pantun_list = [
    "Pergi ngopi di pagi hari,\nDitemani risoles enak banget.\nJangan ragu buat mimpi tinggi,\nSelama kamu terus bergerak!",
    "Jalan-jalan ke Malioboro,\nNaik sepeda sambil tersenyum.\nGagal itu bukan horor bro,\nAsal bangkit dan tetap menyemangkum.",
    "Makan soto pakai lontong,\nDiseruput panas, enaknya pol!\nSemangat terus dong,\nBiar cita-cita nggak molor!"
]

async def pantun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_states.get(update.effective_user.id) != "active":
        return
    bait = random.choice(pantun_list)
    await update.message.reply_text(f"🎭 *Pantun receh dulu ya:*\n\n{bait}", parse_mode=ParseMode.MARKDOWN)

# ======= /curhat =======
async def curhat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "curhat_ai"
    balasan = (
        " *Mode Curhat Yui sudah nyala!*\nhehe\n\n"
        "_Sekarang kamu bisa cerita apa aja, dan Yui bakal bantu jawab sebisanya._\n"
        "Ketik pesanmu dan keluarkan unek-unek kamu disini~ \n\n"
        "Ketik /stop kalau ingin keluar dari mode ini."
    )
    await update.message.reply_text(balasan, parse_mode=ParseMode.MARKDOWN)

# ======= /stop =======
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = "stopped"
    user_contexts.pop(user_id, None)
    await update.message.reply_text("🚫 yui bakal diam dulu ya.\nkalau kamu pengen chat aku lagi, cukup kirim /start ")

# ======= /clearchat =======
async def clearchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        await update.message.reply_text("Fitur ini hanya bisa digunakan di chat pribadi ya 🌷")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Iya", callback_data="confirm_clear"),
            InlineKeyboardButton("❌ Tidak", callback_data="cancel_clear")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚠️ *Yakin ingin menghapus semua chat?*\n\n"
        "_Semua pesan sebelumnya akan dihapus dan tidak bisa dikembalikan._",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# ======= Callback Handler =======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_clear":
        chat_id = query.message.chat_id
        await query.edit_message_text("🧹 Menghapus semua chat...")
        for i in range(query.message.message_id, query.message.message_id - 100, -1):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=i)
            except:
                continue
    elif query.data == "cancel_clear":
        await query.edit_message_text("❎ Oke deh, penghapusan dibatalkan.")

# ======= Message Handler =======
def generate_greeting(name):
    response = [
        f"...hai.",
        f"eh {name} ya... hmm.",
        "ya.",
        "kamu lagi ya...",
        "aku dengerin... tapi males bales.",
        "hmm... ngomong aja sih.",
        "nggak ngerti juga sih, tapi yaudah.",
        "kamu suka roti... nggak?",
        "...yaudah.",
        "...",
        "eh.",
    ]
    return random.choice(response)

async def worldtime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action(ChatAction.TYPING)
    waktu = get_world_times()
    await send_long_message(update, waktu, parse_mode=ParseMode.MARKDOWN)

async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.first_name or "kamu"
    user_message = update.message.text.strip()

    # Check time
    if user_states.get(user_id) != "curhat_ai" and is_time_query(user_message):
    # reasoning
        ai_reply = await asyncio.to_thread(
            ask_ai,
            user_id=user_id,
            user_input=user_message
        )
        await send_long_message(update, ai_reply, parse_mode=ParseMode.HTML)
        return

    # === FOTO ===
    if update.message.photo:
        image_file = await update.message.photo[-1].get_file()
        tmp_dir = tempfile.gettempdir()
        image_path = os.path.join(tmp_dir, f"yui_{user_id}.jpg")
        await image_file.download_to_drive(image_path)
        caption = update.message.caption or ""

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(1.8, 4.5))
        await update.message.reply_text("wait yui analisis dulu ya gambarnya... \nhmm...")
        await asyncio.sleep(random.uniform(1.8, 4.5))

        try:
            ai_reply = await asyncio.to_thread(
                ask_ai,
                user_id=user_id,
                user_input=caption,
                image_path=image_path
            )
            await send_long_message(update, ai_reply, parse_mode=ParseMode.HTML)

        except Exception as e:
            fallback_msg = str(e)
            if "kelelahan" in fallback_msg:  # dari RateLimitError
                await update.message.reply_text("😵‍💫 yui lagi tepar bentar... coba lagi yaa~", parse_mode=ParseMode.MARKDOWN)
            elif "timeout" in fallback_msg.lower():
                await update.message.reply_text("⏳ ehh... yui lama mikirnya... ulangi lagi yaa 😣", parse_mode=ParseMode.MARKDOWN)
            else:
                error_msg = escape_markdown(f"⚠️ maaf ya, yui lagi error: {fallback_msg}", version=2)
                await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN_V2)
        return

    # === TEKS TANPA GAMBAR ===
    if not update.message.text:
        return

    
    state = user_states.get(user_id, "active")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        ai_reply = await asyncio.to_thread(
            ask_ai,
            user_id=user_id,
            user_input=user_message
        )
        await send_long_message(update, ai_reply, parse_mode=ParseMode.HTML)

    
    # Ganti bagian `except Exception as e:` menjadi:
    except Exception as e:
        fallback_msg = str(e)
        if "kelelahan" in fallback_msg:  # dari RateLimitError
            await update.message.reply_text("😵‍💫 Yui lagi tepar bentar... coba lagi yaa~", parse_mode=ParseMode.MARKDOWN)
        elif "timeout" in fallback_msg.lower():
            await update.message.reply_text("⏳ Ehh... Yui lama mikirnya... ulangi lagi yaa 😣", parse_mode=ParseMode.MARKDOWN)
        else:
            error_msg = escape_markdown(f"⚠️ Maaf ya, Yui lagi error: {fallback_msg}", version=2)
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN_V2)

    
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ======= Main =======
def main():
    if TELEGRAM_TOKEN is None:
        print("❌ Error: Token tidak ditemukan di file .env")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("motivasi", motivasi))
    app.add_handler(CommandHandler("quotes", quotes))
    app.add_handler(CommandHandler("pantun", pantun))
    app.add_handler(CommandHandler("curhat", curhat))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("clearchat", clearchat))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, reply_message))
    app.add_handler(CommandHandler("worldtime", worldtime_command))
    app.add_handler(CommandHandler("musikinfo", musikinfo))

    print("✅ Yui Bot aktif dan siap menyapa kamu")
    logging.info("Bot sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()