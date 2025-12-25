import os, telebot, yt_dlp, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "X Downloader is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)

# تخزين حالة المستخدم: 0 = جديد، 1 = ضغط مرة واحدة، verified = تم التفعيل
user_status = {}

# --- 3. نظام التحقق والمتابعة المطور ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # رسالة الترحيب الأولى (بعد حذف سطر Start)
    welcome_text = (
        "اهلا بك 👋🏼\n"
        "شكرا لاستخدامك بوت حفظ السنابات 👻\n"
        "أولا سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت\n\n"
        "Welcome 👋🏼\n"
        "Thank you for using the Snap Saver Bot 👻\n"
        "First, you'll need to follow my Snapchat account to activate the bot"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_follow = types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK)
    btn_confirm = types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="check_v1")
    markup.add(btn_follow)
    markup.add(btn_confirm)
    
    bot.send_message(user_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_logic(call):
    user_id = call.message.chat.id
    
    # الضغطة الأولى: إظهار رسالة "نعتذر منك لم يتم التحقق"
    if call.data == "check_v1":
        error_msg = (
            "نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر تفعيل البوت 🔓\n\n"
            "We apologize, but your Snapchat account follow request has not been verified. ❌👻\n"
            "Please click \"Follow Account\" and you will be redirected to Snapchat. After following, click the \"Activate\" button. 🔓"
        )
        # تغيير الكود الخاص بالزر للخطوة التالية
        markup = types.InlineKeyboardMarkup()
        btn_follow = types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK)
        btn_confirm = types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="check_v2")
        markup.add(btn_follow)
        markup.add(btn_confirm)
        
        bot.edit_message_text(error_msg, user_id, call.message.message_id, reply_markup=markup)

    # الضغطة الثانية: التفعيل النهائي
    elif call.data == "check_v2":
        user_status[user_id] = "verified"
        success_text = (
            "تم تفعيل البوت بنجاح ✅\n"
            "الرجاء ارسال الرابط 🔗\n\n"
            "The bot has been successfully activated ✅ \n"
            "Please send the link 🔗"
        )
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, success_text)

# --- 4. معالج تحميل منصة X ---
@bot.message_handler(func=lambda message: True)
def handle_x(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "x.com" in url or "twitter.com" in url:
        prog = bot.reply_to(message, "جاري التحميل ... ⏳\nLoading... ⏳")
        
        ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                
                if video_url:
                    bot.send_video(user_id, video_url)
                    bot.send_message(user_id, "تم التحميل ✅\nDone ✅")
                    bot.delete_message(user_id, prog.message_id)
                else:
                    raise Exception()
        except:
            bot.edit_message_text("نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌\n\nWe apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌", user_id, prog.message_id)
    else:
        bot.reply_to(message, "الرجاء ارسال رابط الصحيح ❌\nPlease send the correct link ❌")

# --- 5. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()
