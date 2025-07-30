from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
    SourceGroup
)
import os
import time

app = Flask(__name__)

# إعداد التوكن والقناة
LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_SECRET = os.getenv("LINE_SECRET")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# قائمة كلمات الترحيب
trigger_words = ["هلا", "السلام", "اهلا", "هاي", "مرحبا", "صباح الخير", "مساء الخير"]

# حالة التشغيل/الإيقاف للقروبات
group_status = {}
last_seen = {}
cooldown = 300  # بالثواني

@app.route("/", methods=['GET'])
def index():
    return "🤖 LINE bot is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        if not isinstance(event.source, SourceGroup):
            return  # نرد فقط داخل المجموعات

        gid = event.source.group_id
        uid = event.source.user_id
        text = event.message.text.lower()

        # التحكم بالتشغيل والإيقاف
        if text == "!تشغيل":
            group_status[gid] = True
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ تم تفعيل الرد."))
            return
        elif text == "!إيقاف":
            group_status[gid] = False
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🛑 تم إيقاف الرد."))
            return

        if not group_status.get(gid, True):
            return  # الرد متوقف

        # الرد التلقائي
        if any(word in text for word in trigger_words):
            now = time.time()
            if uid not in last_seen or now - last_seen[uid] > cooldown:
                profile = line_bot_api.get_group_member_profile(gid, uid)
                name = profile.display_name
                picture_url = profile.picture_url

                messages = [
                    TextSendMessage(text=f"👋 تم رصدك بلطف يا {name}، أهلًا بك معنا!")
                ]

                if picture_url:
                    messages.insert(0, ImageSendMessage(original_content_url=picture_url, preview_image_url=picture_url))

                line_bot_api.reply_message(event.reply_token, messages)
                last_seen[uid] = now

    except Exception as e:
        print(f"[❌ خطأ]: {e}")

if __name__ == "__main__":
    app.run()
