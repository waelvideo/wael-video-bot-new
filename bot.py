import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@w24symedad"


async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 اشترك بالقناة",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ تحقّق من الاشتراك",
                callback_data="check"
            )
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك\n\n"
        "🔒 لاستخدام البوت يجب الاشتراك بقناتنا أولاً.\n\n"
        "بعد الاشتراك اضغط «تحقّق من الاشتراك» ثم أرسل الفيديو.",
        reply_markup=buttons()
    )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_subscribed(query.from_user.id, context):
        await query.edit_message_text(
            "✅ تم التحقق من اشتراكك!\n\n"
            "📥 الآن أرسل الفيديو."
        )
    else:
        await query.edit_message_text(
            "❌ لم تشترك بالقناة بعد.\n\n"
            "اشترك ثم اضغط «تحقّق من الاشتراك».",
            reply_markup=buttons()
        )


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            "🔒 يجب الاشتراك بالقناة أولاً.",
            reply_markup=buttons()
        )
        return

    await update.message.reply_text("⏳ جاري إرسال الفيديو...")

    await update.message.reply_video(
        video=update.message.video.file_id,
        caption="✅ تفضل الفيديو"
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN غير موجود في أسرار GitHub")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check, pattern="^check$"))
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))

    print("البوت يعمل...")
    app.run_polling()


if __name__ == "__main__":
    main()
