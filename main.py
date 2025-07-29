from linepy import *
import time
from akad.ttypes import Mention
import os

# تسجيل الدخول من QR (لا يمكن على Render)
# في Render يجب استخدام LoginToken أو إعادة استخدام session

# ❗ قم بتسجيل الدخول محليًا أولًا واحفظ التوكن يدويًا ثم ضعه هنا:
LINE_TOKEN = os.getenv("LINE_TOKEN")

# تسجيل الدخول باستخدام التوكن
cl = LINE(authToken=LINE_TOKEN)
print(f"✅ تسجيل الدخول كـ: {cl.profile.displayName}")

oepoll = OEPoll(cl)

# كلمات الترحيب
trigger_words = ["هلا", "السلام", "اهلا", "هاي", "مرحبا", "صباح الخير", "مساء الخير"]

# للتحكم في حالة التشغيل/الإيقاف للقروبات
group_status = {}

# لتقليل التكرار
last_seen = {}
cooldown_seconds = 300  # 5 دقائق

def send_mention(to, text, mid):
    name = cl.getContact(mid).displayName
    name_index = text.index(f"@{name}")
    mention_data = [{"S": str(name_index), "E": str(name_index + len(name)), "M": mid}]
    cl.sendMessage(to, text, contentMetadata={"MENTION": str({"MENTIONEES": mention_data})}, contentType=0)

def auto_reply(op):
    try:
        if op.type != 26:
            return

        msg = op.message
        gid = msg.to
        uid = msg._from
        text = msg.text.lower() if msg.text else ""

        if msg.toType != 2:  # نريد القروبات فقط
            return

        # أوامر التشغيل والإيقاف
        if text == "!تشغيل":
            group_status[gid] = True
            cl.sendMessage(gid, "✅ تم تفعيل الرد التلقائي.")
            return
        elif text == "!إيقاف":
            group_status[gid] = False
            cl.sendMessage(gid, "🛑 تم إيقاف الرد التلقائي.")
            return

        # إذا القروب غير مفعل حالياً، تجاهل
        if not group_status.get(gid, True):
            return

        # تحقق من الكلمات
        if any(word in text for word in trigger_words):
            now = time.time()
            if uid not in last_seen or now - last_seen[uid] > cooldown_seconds:
                contact = cl.getContact(uid)
                name = contact.displayName
                picture_url = contact.pictureStatus

                if picture_url:
                    cl.sendImageWithURL(gid, f"http://dl.profile.line.naver.jp/{picture_url}")

                message = f"👋 تم رصدك بلطف يا @{name}، أهلًا بك معنا!"
                send_mention(gid, message, uid)
                last_seen[uid] = now

    except Exception as e:
        print(f"[❌ خطأ] {e}")

# التشغيل
while True:
    try:
        ops = oepoll.singleTrace(count=50)
        for op in ops:
            auto_reply(op)
            oepoll.setRevision(op.revision)
    except Exception as e:
        print(f"[❌ خطأ رئيسي] {e}")
