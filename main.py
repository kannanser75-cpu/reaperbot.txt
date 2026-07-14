import asyncio
import logging
import os
import http.client
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters, ContextTypes

# ലോഗ്സ് സെറ്റപ്പ്
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ബോട്ട് വിവരങ്ങൾ
BOT_TOKEN = "8842459355:AAEJT2zbVvmhNUCgmTQtXc2Ao7B_ChZYDMQ"
GROUP_CHAT_ID = "ഇവിടെ_നിങ്ങളുടെ_ഗ്രൂപ്പ്_ഐഡി_നൽകുക" # നിങ്ങളുടെ -100 എന്ന് തുടങ്ങുന്ന ഐഡി ഇവിടെ മാറ്റുക
LINK_TO_SEND = "https://t.me/+lZgpL5ALAxtlNTM1"

PORT = int(os.environ.get("PORT", 8080))

# --- വെബ് സെർവർ സെറ്റപ്പ് ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is Running!")
    def log_message(self, format, *args): return

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# --- 5 മിനിറ്റിൽ പിങ് ചെയ്യുന്ന ഫങ്ക്ഷൻ ---
async def self_ping_task():
    await asyncio.sleep(10)
    while True:
        try:
            conn = http.client.HTTPConnection(f"127.0.0.1:{PORT}")
            conn.request("GET", "/")
            conn.close()
        except: pass
        await asyncio.sleep(300)

# --- ഓട്ടോ റിയാക്ഷൻ (💋, 🍓) ---
async def auto_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            # നിങ്ങൾ ആവശ്യപ്പെട്ട 💋 അല്ലെങ്കിൽ 🍓 ഇതിൽ ഒരെണ്ണം റാൻഡം ആയി തിരഞ്ഞെടുക്കും
            selected_emoji = random.choice(["💋", "🍓"])
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.id,
                reaction=[{"type": "emoji", "emoji": selected_emoji}]
            )
        except Exception as e:
            logging.error(f"റിയാക്ഷൻ ഇടാൻ കഴിഞ്ഞില്ല: {e}")

# --- മറ്റ് ഫങ്ക്ഷനുകൾ ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ഹായ്! ഞാൻ ആക്ടീവ് ആണ്. 💋🍓")

async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.user_id
    try:
        await context.bot.approve_chat_join_request(chat_id=update.chat_join_request.chat.id, user_id=user_id)
    except: pass

async def repeater_task(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    job = context.job
    if job.data:
        try: await bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=job.data)
        except: pass
    try:
        msg = await bot.send_message(chat_id=GROUP_CHAT_ID, text=LINK_TO_SEND)
        job.data = msg.message_id
    except Exception as e:
        logging.error(f"ലിങ്ക് അയക്കാൻ പറ്റിയില്ല: {e}")

# --- Python 3.14 പൊരുത്തക്കേട് ഒഴിവാക്കാൻ മെയിൻ റണ്ണർ മാറ്റുന്നു ---
async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(ChatJoinRequestHandler(approve_join_request))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_react))

    job_queue = application.job_queue
    job_queue.run_repeating(repeater_task, interval=60, first=1, data=None)

    asyncio.create_task(self_ping_task())

    # പുതിയ പൈത്തൺ വേർഷനുകളിൽ ക്രാഷ് ആകാതിരിക്കാൻ മാനുവൽ സെറ്റപ്പ്
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logging.info("ബോട്ട് വിജയകരമായി റൺ ആയിരിക്കുന്നു...")
    
    # ബോട്ട് എപ്പോഴും റൺ ചെയ്തുകൊണ്ടിരിക്കാൻ
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        pass
