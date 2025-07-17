
# 🧠 Yui-Bot (V-1.0)

Yui adalah chatbot Telegram dengan kepribadian **tsundere**, **dry-text**, dan sedikit pemalu. Terinspirasi dari karakter **Yui Hirasawa (K-ON!)**, bot ini dirancang untuk merespons pengguna dengan gaya manusiawi, tidak sok AI, dan cocok buat tempat curhat diam-diam.

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🧍‍♀️ Karakter Tsundere | Bot berbicara cuek, dry-text, kadang canggung dan malu-malu |
| 💬 /curhat | Mode spesial untuk curhat dengan tone lebih personal dan lowercase |
| 🧠 Memory | Bot mengingat histori chat pengguna, auto-trim jika terlalu panjang |
| 🌈 Random Fun | Command seperti `/motivasi`, `/quotes`, `/pantun` |
| 🧹 /clearchat | Hapus memory chat dengan konfirmasi tombol inline |
| 🤖 Bebas AI Vibes | Respons dibersihkan dari ciri khas AI, seperti kata “Sebagai AI…” |

---

## 🛠️ Setup Lokal

### 1. Clone Repo
```bash
git clone https://github.com/bondanbanuaji/yuibot-v1.gi
cd yui-telegram-bot
```

### 2. Install Dependency
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi `.env`
Buat file `.env` di root folder dengan isi seperti ini:
```
TELEGRAM_BOT_TOKEN = your_telegram_bot_token_here
GEMINI_API_KEY = your_gemini_api_key_here
```

---

## 🧪 Struktur File

```
├── ai.py            # Modul utama yang handle prompt & respons Yui
├── bot.py           # Setup Telegram Bot + command handler
├── requirements.txt # Semua dependency
├── .env             # Token dan API Key
```

---

## 💡 Contoh Command

- `/start` → Yui menyapa kamu dengan gaya canggung
- `/curhat` → Masuk mode curhat (ngobrol lowercase, lebih emosional)
- `/quotes`, `/pantun`, `/motivasi` → Random kata-kata
- `/clearchat` → Hapus memori interaksi (ada tombol konfirmasi)
- Cukup kirim teks biasa juga bisa (Yui tetap responsif~)

---

## 🚧 Notes

- Karakter Yui bisa diedit lebih lanjut di `ai.py`
- Menggunakan Google Gemini API untuk reasoning
- Memory user disimpan di dict selama runtime (tidak persist)

---

## 📸 Screenshot Preview

<p align="center">
  <img src="/img/preview.jpeg" width="300">
</p>

---

## 📄 Lisensi

MIT License - silakan gunakan, modifikasi, atau fork sesukamu 💫  
Karakter Yui Hirasawa © Kyoto Animation (non-komersial tribute)

---
