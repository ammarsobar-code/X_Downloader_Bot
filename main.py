import os, telebot, yt_dlp, time, sys, subprocess, shutil
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "X Video Direct Downloader Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. وظيفة التنظيف التلقائي (Auto-Clean) ---
def auto_clean_environment():
    """تنظيف الذاكرة وقتل العمليات العالقة لضمان استقرار البوت"""
    try:
        # مسح ذاكرة التخزين المؤقت لـ yt-dlp
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        
        # قتل أي عمليات yt-dlp أو ffmpeg معلقة تستهلك الرام
        if os.name != 'nt':
            subprocess.run(["pkill", "-9", "-f", "yt-dlp"], stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "ffmpeg"], stderr=subprocess.DEVNULL)
            
        # تنظيف مجلد التحميلات إذا وُجد
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
            os.makedirs("downloads", exist_ok=True)
    except:
        pass

# --- 3. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 4. نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع منصة اكس\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "Thank you for using X Downloader Bot\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account to activate the bot</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗</b>", parse_mode='HTML')

# --- 5. معالج التحميل المطور مع نظام التنظيف ---
@bot.message_handler(func=lambda message: True)
def handle_x_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "x.com" in url or "twitter.com" in url:
        prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
        
        # إعدادات متطورة لمنع استهلاك الموارد
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'cachedir': False, # تعطيل الكاش على القرص
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                found_any_video = False

                if 'entries' in info:
                    for entry in info['entries']:
                        video_url = entry.get('url')
                        if video_url and (entry.get('vcodec') != 'none' or '.mp4' in video_url):
                            bot.send_video(user_id, video_url)
                            found_any_video = True
                
                elif info.get('url'):
                    video_url = info.get('url')
                    if info.get('vcodec') != 'none' or '.mp4' in video_url:
                        bot.send_video(user_id, video_url)
                        found_any_video = True

                if found_any_video:
                    bot.send_message(user_id, "<b>تم التحميل ✅\nDone ✅</b>", parse_mode='HTML')
                    bot.delete_message(user_id, prog.message_id)
                else:
                    bot.edit_message_text("<b>❌ لم يتم العثور على فيديوهات.</b>", user_id, prog.message_id, parse_mode='HTML')

        except Exception:
            error_tech = (
                "<b>نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌</b>\n\n"
                "<b>Technical issue occurred ❌</b>"
            )
            bot.edit_message_text(error_tech, user_id, prog.message_id, parse_mode='HTML')
        
        finally:
            # --- الإضافة الجوهرية: التنظيف الإجباري بعد كل طلب ---
            auto_clean_environment()
            
    else:
        bot.reply_to(message, "<b>الرجاء ارسال الرابط الصحيح ❌</b>", parse_mode='HTML')

# --- 6. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    auto_clean_environment() # تنظيف أولي عند بدء التشغيل
    try:
        bot.remove_webhook()
    except: pass
    time.sleep(1)
    print("X Bot is starting...")
    # استخدام بولينج معزز لضمان استمرارية الاتصال
    bot.infinity_polling(timeout=20, long_polling_timeout=10, restart_on_change=False)
