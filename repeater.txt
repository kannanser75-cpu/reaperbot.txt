import asyncio
import logging
import os
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, CommandHandler, ContextTypes

# ലോഗ്സ് സെറ്റപ്പ്
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ബോട്ട് വിവരങ്ങൾ
BOT_TOKEN = "8842459355:AAEJT2zbVvmhNUCgmTQtXc2Ao7B_ChZYDMQ"
GROUP_CHAT_ID = "ഇവിടെ_നിങ്ങളുടെ_ഗ്രൂപ്പ്_ഐഡി_നൽകുക" # റോസ് ബോട്ട് വഴി കിട്ടിയ ഐഡി ഇവിടെ നൽകുക
LINK_TO_SEND = "https://t.me/+lZgpL5ALAxtlNTM1"

# റെൻഡർ നൽകുന്ന പോർട്ട് എടുക്കുന്നു, ഫ്രീ സർവീസിന് ഇത് നിർബന്ധമാണ്
PORT = int(os.environ.get("PORT", 8080))

# --- റെൻഡറിന് വേണ്ടി ഒരു വെബ് സെർവർ സെറ്റപ്പ് ചെയ്യുന്നു ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

    # ലോഗ്സ് ക്ലീൻ ആയിരിക്കാൻ വെറുതെ വരുന്ന റിക്വസ്റ്റുകളുടെ ലോഗ് ഒഴിവാക്കുന്നു
    def log_message(self, format, *args):
        return

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    logging.info(f"Health check server started on port {PORT}")
    server.serve_forever()

# --- ബോട്ട് ഉറങ്ങിപ്പോകാതിരിക്കാൻ 5 മിനിറ്റിൽ തനിയെ പിങ് ചെയ്യുന്ന ഫങ്ക്ഷൻ ---
async def self_ping_task():
    await asyncio.sleep(10) # ബോട്ട് സ്റ്റാർട്ട് ആയി വരാൻ കുറച്ചു സമയം നൽകുന്നു
    while True:
        try:
            # ലോക്കൽ ഹോസ്റ്റിലേക്ക് തന്നെ ഒരു റിക്വസ്റ്റ് അയക്കുന്നു
            conn = http.client.HTTPConnection(f"127.0.0.1:{PORT}")
            conn.request("GET", "/")
            response = conn.getresponse()
            if response.status == 200:
                logging.info("Self-Ping വിജയകരമായി നടന്നു. ബോട്ട് ആക്ടീവ് ആണ്!")
            conn.close()
        except Exception as e:
            logging.error(f"Self-Ping ചെയ്യുന്നതിൽ പരാജയം: {e}")
        
        # ഓരോ 5 മിനിറ്റിലും പിങ് ചെയ്യുന്നു (5 * 60 = 300 സെക്കൻഡ്)
        await asyncio.sleep(300)

# --- ഡിഎമ്മിൽ /start അടിക്കുമ്പോൾ തിരിച്ചു ഹായ് അയക്കാനുള്ള ഫങ്ക്ഷൻ ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ഹായ്! ഞാൻ ആക്ടീവ് ആണ്. സുഗമമായി പ്രവർത്തിക്കുന്നുണ്ട്! 👍")
    logging.info(f"യൂസർ {update.message.from_user.id} ബോട്ട് സ്റ്റാർട്ട് ചെയ്തു പരിശോധിച്ചു.")

# --- പുതിയ മെമ്പർമാരെ തനിയെ അപ്രൂവ് ചെയ്യാനുള്ള ഫങ്ക്ഷൻ ---
async def approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.user_id
    chat_id = update.chat_join_request.chat.id
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
        logging.info(f"പുതിയ മെമ്പറെ അപ്രൂവ് ചെയ്തു: {user_id}")
    except Exception as e:
        logging.error(f"അപ്രൂവ് ചെയ്യുന്നതിൽ പരാജയപ്പെട്ടു: {e}")

# --- ഓരോ മിനിറ്റിലും ലിങ്ക് അയക്കാനും പഴയത് കളയാനുമുള്ള ഫങ്ക്ഷൻ ---
async def repeater_task(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    job = context.job
    
    if job.data:
        try:
            await bot.delete_message(chat_id=GROUP_CHAT_ID, message_id=job.data)
            logging.info("പഴയ ലിങ്ക് ഡിലീറ്റ് ചെയ്തു.")
        except Exception as e:
            logging.error(f"പഴയ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാൻ പറ്റിയില്ല: {e}")

    try:
        msg = await bot.send_message(chat_id=GROUP_CHAT_ID, text=LINK_TO_SEND)
        job.data = msg.message_id
        logging.info("പുതിയ ലിങ്ക് അയച്ചു!")
    except Exception as e:
        logging.error(f"മെസ്സേജ് അയക്കാൻ കഴിഞ്ഞില്ല: {e}")

if __name__ == '__main__':
    # വെബ് സെർവർ പശ്ചാത്തലത്തിൽ (Background thread) റൺ ചെയ്യുന്നു
    server_thread = threading.Thread(target=run_health_server, daemon=True)
    server_thread.start()

    # ടെലിഗ്രാം ബോട്ട് സെറ്റപ്പ്
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # കമാൻഡ് ഹാൻഡ്‌ലറുകൾ
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(ChatJoinRequestHandler(approve_join_request))

    # ലിങ്ക് റീപ്പീറ്റ് ചെയ്യാനുള്ള ജോബ് (60 സെക്കൻഡ്)
    job_queue = application.job_queue
    job_queue.run_repeating(repeater_task, interval=60, first=1, data=None)

    # ബോട്ട് തനിയെ പിങ് ചെയ്യാനുള്ള ലൂപ്പ് അസിൻക്രണസ് ആയി റൺ ചെയ്യുന്നു
    loop = asyncio.get_event_loop()
    loop.create_task(self_ping_task())

    logging.info("ബോട്ട് റൺ ആകാൻ തയ്യാറാണ്...")
    application.run_polling()
