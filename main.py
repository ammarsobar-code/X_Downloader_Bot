import os, telebot, yt_dlp, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "X Video Direct Downloader"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق برسائل منفصلة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "اهلا بك 👋🏼\n"
        "شكرا لاستخدامك بوت تحميل مقاطع منصة اكس \n"
        "أولا سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت\n\n"
        "Welcome 👋🏼\n"
        "Thank you for using X Download Bot \n"
        "First, you'll need to follow my Snapchat account to activate the bot"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "step_1":
        fail_msg = (
            "نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر تفعيل البوت 🔓\n\n"
            "We apologize, but your Snapchat account follow request has not been verified. ❌👻\n"
            "Please click \"Follow Account\" and you will be redirected to Snapchat. After following, click the \"Activate\" button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup)
    elif call.data == "step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗\n\nThe bot has been successfully activated ✅\nPlease send the link 🔗")

# --- 4. معالج التحميل (إرسال فيديوهات منفصلة) ---
@bot.message_handler(func=lambda message: True)
def handle_x_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "x.com" in url or "twitter.com" in url:
        prog = bot.reply_to(message, "جاري التحميل ... ⏳\nLoading... ⏳")
        
        # خيارات جلب الفيديو فقط بأفضل جودة
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                found_any_video = False

                # إذا كانت التغريدة تحتوي على قائمة فيديوهات
                if 'entries' in info:
                    for entry in info['entries']:
                        video_url = entry.get('url')
                        # نتحقق أن الرابط فيديو فعلاً
                        if video_url and (entry.get('vcodec') != 'none' or '.mp4' in video_url):
                            bot.send_video(user_id, video_url)
                            found_any_video = True
                
                # إذا كانت التغريدة فيديو واحد
                elif info.get('url'):
                    video_url = info.get('url')
                    if info.get('vcodec') != 'none' or '.mp4' in video_url:
                        bot.send_video(user_id, video_url)
                        found_any_video = True

                if found_any_video:
                    bot.send_message(user_id, "تم التحميل ✅\nDone ✅")
                else:
                    bot.edit_message_text("❌ لم يتم العثور على فيديوهات في هذا الرابط.", user_id, prog.message_id)
                
                bot.delete_message(user_id, prog.message_id)

        except Exception as e:
            bot.edit_message_text("نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌\n\nWe apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌", user_id, prog.message_id)
    else:
        bot.reply_to(message, "الرجاء ارسال رابط الصحيح ❌\nPlease send the correct link ❌")

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
