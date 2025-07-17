import os
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# Load token dari .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Penyimpanan status user
user_states = {}

# ======= /start =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_states[user_id] = "active"
    name = user.first_name if user else "teman baru"

    await update.message.reply_animation(
        animation="https://media1.tenor.com/m/ohxROUA8aW0AAAAd/shy-cute.gif"
    )

    welcome_text = (
        f"🌸 Hai, *{name}*~\n\n"
        "Namaku *Yui*, dan aku di sini buat nemenin kamu ngobrol, semangatin, atau sekadar dengerin curhatanmu 🫶\n\n"
        "✨ Cukup kirim pesan apa aja, nanti Yui balas dengan gaya Yui~\n"
        "📌 Cobain juga beberapa perintah seru:\n"
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
motivasi_list = [
    "🔥 *Jangan nyerah ya!* Hal besar butuh proses, bukan keajaiban instan.",
    "🌟 *Kamu tuh keren*, cuma kadang lupa aja.",
    "🚀 Maju terus! Mimpi kamu nggak bakal jalan kalau kamu diem aja.",
    "📈 Gagal itu bukan akhir, tapi awal dari cerita hebat kamu.",
    "💡 Hujan boleh deras, tapi kamu tetap bisa nari di tengahnya. Semangat!"
]

async def motivasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_states.get(update.effective_user.id) != "active":
        return
    kata = random.choice(motivasi_list)
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
    if user_states.get(update.effective_user.id) != "active":
        return
    balasan = (
        "🫂 Cerita aja, aku di sini kok.\n"
        "Kadang cukup didengerin aja udah bikin lega. Gausah ragu, aku gak bakal nge-judge apa pun yang kamu rasa 💗"
    )
    await update.message.reply_text(balasan, parse_mode=ParseMode.MARKDOWN)

# ======= /stop =======
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = "stopped"
    await update.message.reply_text(
        "🚫 Yui bakal diam dulu ya.\nKalau kamu butuh aku lagi, cukup kirim /start 🌸"
    )

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

# ======= Balasan Pesan Biasa =======
async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_states.get(user.id) != "active":
        return

    name = user.first_name if user else "kamu"
    user_message = update.message.text
    print(f"[{name}] mengetik: {user_message}")

    reply = f"📩 *{name}*, kamu bilang:* \"_{user_message}_\"*\n\nYui dengerin, loh~ 😊"
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

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
    app.add_handler(CallbackQueryHandler(button_handler))  # <- penting!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_message))

    print("✅ Yui Bot aktif dan siap menyapa kamu 🌸")
    app.run_polling()

if __name__ == "__main__":
    main()