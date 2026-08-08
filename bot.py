import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ضع توكن البوت في Secrets باسم BOT_TOKEN
TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        return

    await update.message.reply_text(
        "أهلاً بك 👋\n"
        "أرسل لي فيديو وسأستقبله."
    )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بعض تحديثات تيليغرام قد لا يكون معها مستخدم
    if update.effective_user is None:
        return

    # نتأكد أن الرسالة موجودة
    if update.message is None:
        return

    user_id = update.effective_user.id

    # إذا كان المستخدم أرسل فيديو
    if update.message.video:
        video = update.message.video

        await update.message.reply_text(
            f"تم استلام الفيديو ✅\n"
            f"معرّف المستخدم: {user_id}\n"
            f"حجم الفيديو: {video.file_size or 'غير معروف'} بايت"
        )

    # إذا أرسل فيديو كملف
    elif update.message.document:
        await update.message.reply_text(
            "تم استلام الملف ✅"
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"حدث خطأ: {context.error}")


def main():
    if not TOKEN:
        raise ValueError(
            "لم يتم العثور على BOT_TOKEN. "
            "أضف التوكن في Secrets باسم BOT_TOKEN."
        )

    application = Application.builder().token(TOKEN).build()

    # أمر /start
    application.add_handler(
        CommandHandler("start", start)
    )

    # استقبال الفيديو
    application.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            receive_video
        )
    )

    # معالجة الأخطاء
    application.add_error_handler(error_handler)

    print("البوت يعمل الآن...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
