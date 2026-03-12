import json
import random
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8714667202:AAEtFxDowWh8cWmeCHuHr_fO8SWcF_500lM"

POSTS_FILE = "posts.json"

logging.basicConfig(level=logging.INFO)

scheduler = AsyncIOScheduler()

def load_data():
    try:
        with open(POSTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"channels": [], "posts": [], "interval": 24}

def save_data(data):
    with open(POSTS_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اهلا بك في بوت النشر التلقائي\n\n"
        "/addchannel @channel\n"
        "/schedule 6\n"
        "/postnow"
    )

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب معرف القناة بعد الأمر")
        return

    channel = context.args[0]

    if channel not in data["channels"]:
        data["channels"].append(channel)
        save_data(data)
        await update.message.reply_text("تمت إضافة القناة")
    else:
        await update.message.reply_text("القناة مضافة مسبقا")

async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = {}

    if update.message.text:
        post["type"] = "text"
        post["content"] = update.message.text

    elif update.message.photo:
        post["type"] = "photo"
        post["content"] = update.message.photo[-1].file_id
        post["caption"] = update.message.caption

    else:
        return

    data["posts"].append(post)
    save_data(data)

    await update.message.reply_text("تم حفظ المنشور")

async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await publish_post(context)
    await update.message.reply_text("تم النشر")

async def publish_post(context: ContextTypes.DEFAULT_TYPE):
    if not data["posts"]:
        return

    post = random.choice(data["posts"])

    for channel in data["channels"]:
        try:
            if post["type"] == "text":
                await context.bot.send_message(channel, post["content"])

            elif post["type"] == "photo":
                await context.bot.send_photo(
                    channel,
                    post["content"],
                    caption=post.get("caption")
                )

        except Exception as e:
            print(e)

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب عدد الساعات")
        return

    hours = int(context.args[0])

    data["interval"] = hours
    save_data(data)

    scheduler.remove_all_jobs()

    scheduler.add_job(
        publish_post,
        "interval",
        hours=hours,
        args=[context]
    )

    await update.message.reply_text(f"تم ضبط النشر كل {hours} ساعات")

async def delete_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["posts"]:
        await update.message.reply_text("لا توجد منشورات")
        return

    data["posts"].pop()
    save_data(data)

    await update.message.reply_text("تم حذف آخر منشور")

async def scheduled_post():
    if not data["posts"]:
        return

    post = random.choice(data["posts"])

    app = ApplicationBuilder().token(TOKEN).build()

    for channel in data["channels"]:
        try:
            if post["type"] == "text":
                await app.bot.send_message(channel, post["content"])

            elif post["type"] == "photo":
                await app.bot.send_photo(
                    channel,
                    post["content"],
                    caption=post.get("caption")
                )

        except:
            pass

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("postnow", post_now))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("delete", delete_post))

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, save_post))

    scheduler.add_job(
        scheduled_post,
        "interval",
        hours=data["interval"]
    )

    scheduler.start()

    print("Bot started")

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
