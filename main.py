import asyncio
import logging
import os
import http.client
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- നിങ്ങളുടെ വിവരങ്ങൾ ---
BOT_TOKEN = "8842459355:AAEJT2zbVvmhNUCgmTQtXc2Ao7B_ChZYDMQ"
GROUP_CHAT_ID = -1003872572810  
LINK_TO_SEND = "https://t.me/+lZgpL5ALAxtlNTM1"
# --------------------------------------------------

PORT = int(os.environ.get("PORT", 8080))

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

async def self_ping_task():
    await asyncio.sleep(10)
    while True:
        try:
            conn = http.client.HTTPConnection(f"127.0.0.1:{PORT}")
            conn.request("GET", "/")
            conn.close()
        except: pass
        await asyncio.sleep(300)

# --- തിരുത്തിയ ഓട്ടോ റിയാക്ഷൻ ഫങ്ക്ഷൻ ---
async def auto_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            selected_emoji = random.choice(["💋", "🍓"])
            # പുതിയ ലൈബ്രറി വേർഷന് അനുയോജ്യമായ രീതിയിൽ മാറ്റിയത്:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.id,
                reaction=ReactionTypeEmoji(emoji=selected_emoji)
            )
        except Exception as e:
            logging.error(f"റിയാക്ഷൻ ഇടാൻ കഴിഞ്ഞില്ല: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ഹായ്! ഞാൻ ആക്ടീവ് ആണ്. 💋🍓")

async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.approve_chat_join_request(chat_id=update.chat_join_request.chat.id, user_id=update.chat_join_request.user_id)
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

async def start_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(ChatJoinRequestHandler(approve_join_request))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), auto_react))
    
    application.job_queue.run_repeating(repeater_task, interval=60, first=1, data=None)
    asyncio.create_task(self_ping_task())
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    asyncio.run(start_bot())
