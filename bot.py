import os
import re
import tempfile

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import yt_dlp


TOKEN = os.getenv("BOT_TOKEN")

# قناة الاشتراك
CHANNEL_USERNAME = "@w24symedad"


def extract_url(text):
    if not text:
        return None

    pattern = r"https?://[^\s]+"
    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return None


async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:
        print("Subscription check error:", e)
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.message is None:
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "📢 اشترك بالقناة",
                url="https://t.me/w24symedad"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ تحقق من الاشتراك",
                callback_data="check_subscription"
            )
        ]
    ]

    await update.message.reply_text(
        "أهلاً بك 👋\n\n"
        "لتحميل الفيديو، لازم تشترك بقناتنا أولاً 📢\n\n"
        "بعد الاشتراك اضغط على «تحقق من الاشتراك» ✅",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def check_subscription_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query is None or query.from_user is None:
        return

    await query.answer()

    user_id = query.from_user.id

    subscribed = await is_subscribed(
        user_id,
        context
    )

    if subscribed:
        await query.edit_message_text(
            "✅ تم التحقق من اشتراكك!\n\n"
            "الآن أرسل رابط الفيديو من TikTok أو Instagram أو YouTube."
        )

    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 اشترك بالقناة",
                    url="https://t.me/w24symedad"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 تحقق مرة ثانية",
                    callback_data="check_subscription"
                )
            ]
        ]

        await query.edit_message_text(
            "❌ ما زلت غير مشترك بالقناة.\n\n"
            "اشترك أولاً ثم اضغط «تحقق مرة ثانية» 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def download_video(url):
    temp_dir = tempfile.mkdtemp()

    output_template = os.path.join(
        temp_dir,
        "%(title).80s.%(ext)s"
    )

    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(info)

            if os.path.exists(filename):
                return filename

            # أحياناً yt-dlp يحوّل الامتداد إلى mp4
            base = os.path.splitext(filename)[0]
            mp4_file = base + ".mp4"

            if os.path.exists(mp4_file):
                return mp4_file

        return None

    except Exception as e:
        print("Download error:", e)
        return None


async def receive_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user is None:
        return

    if update.message is None:
        return

    user_id = update.effective_user.id
    text = update.message.text or ""

    url = extract_url(text)

    if not url:
        await update.message.reply_text(
            "❌ أرسل رابط فيديو صحيح من TikTok أو Instagram أو YouTube."
        )
        return

    # التحقق من الاشتراك قبل التحميل
    subscribed = await is_subscribed(
        user_id,
        context
    )

    if not subscribed:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 اشترك بالقناة",
                    url="https://t.me/w24symedad"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ تحقق من الاشتراك",
                    callback_data="check_subscription"
                )
            ]
        ]

        await update.message.reply_text(
            "🔒 لازم تشترك بالقناة أولاً حتى أقدر أحمل لك الفيديو.\n\n"
            "اشترك ثم اضغط «تحقق من الاشتراك» 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    status_message = await update.message.reply_text(
        "⏳ جاري تحميل الفيديو..."
    )

    filename = await download_video(url)

    if not filename or not os.path.exists(filename):
        await status_message.edit_text(
            "❌ ما قدرت أحمل الفيديو.\n\n"
            "تأكد أن الرابط عام وصحيح وحاول مرة ثانية."
        )
        return

    try:
        await status_message.edit_text(
            "📤 تم التحميل، جاري إرسال الفيديو..."
        )

        with open(filename, "rb") as video:
            await update.message.reply_video(
                video=video,
                supports_streaming=True
            )

        await status_message.delete()

    except Exception as e:
        print("Send error:", e)

        await status_message.edit_text(
            "❌ حصل خطأ أثناء إرسال الفيديو.\n"
            "قد يكون حجم الفيديو كبيراً جداً."
        )

    finally:
        try:
            os.remove(filename)
            os.rmdir(os.path.dirname(filename))
        except Exception:
            pass


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    print("Bot error:", context.error)


def main():
    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN غير موجود في Secrets"
        )

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(
            check_subscription_callback,
            pattern="^check_subscription$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_link
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()    
