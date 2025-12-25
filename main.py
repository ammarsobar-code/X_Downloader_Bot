import os, telebot, yt_dlp
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "X/Twitter Downloader is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
# ضع توكن بوت إكس الجديد في الـ Environment Variables
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    msg = f"⚠️ يرجى متابعة حسابي أولاً لتفعيل البوت:\nPlease follow first:\n\n{SNAP_LINK}"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ لم يتم التحقق بعد، تأكد من المتابعة:\n\n{SNAP_LINK}", reply_markup=markup)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت! أرسل رابط تغريدة (X) الآن")

# --- 4. معالج تحميل فيديوهات وصور إكس ---
@bot.message_handler(func=lambda message: True)
def handle_x(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    # دعم روابط x.com و twitter.com
    if "x.com" in url or "twitter.com" in url:
        prog = bot.reply_to(message, "⏳ جاري جلب المحتوى من إكس... | Downloading...")
        
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # التعامل مع الفيديو
                if 'url' in info:
                    video_url = info['url']
                    bot.send_video(user_id, video_url, caption="✅ تم التحميل من إكس")
                
                # التعامل مع الصور (إذا كانت التغريدة تحتوي على صور فقط)
                elif 'entries' in info:
                    for entry in info['entries']:
                        bot.send_photo(user_id, entry['url'])
                
                bot.delete_message(user_id, prog.message_id)
                
        except Exception as e:
            bot.edit_message_text("❌ عذراً، التغريدة قد تكون خاصة أو الرابط غير صحيح.", user_id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط تغريدة صحيح من منصة X.")

# --- 5. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    print("X Bot is starting...")
    bot.infinity_polling()
