from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Yui-Bot is running..."

def run_bot():
    os.system("python bot.py")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=10000)