from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

import requests, logging, asyncio
# run ".\glepbot-env\Scripts\activate" everytime

# to fetch the time
from datetime import datetime

# fetches the token from "token.txt"
token = None
with open("token.txt") as f: 
    token = f.read().strip()

# enabling logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# storing preferences
user_intervals = {}

# helper function to fetch BTC price
def fetch_btc_price_message():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur"
    response = requests.get(url).json()
    usd_price = response['bitcoin']['usd']
    eur_price = response['bitcoin']['eur']
    timestamp = datetime.now().strftime("%H:%M:%S")

    return (
        f" 💰 Current Bitcoin Price:\n"
        f"\n"
        f" USD: ${usd_price}\n"
        f" EUR: €{eur_price}\n"
        f"\n"
        f"fetched at {timestamp}"
    )

# helper function to get the Ethereum price with ohcl
def fetch_eth_price_message():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd,eur"
    response = requests.get(url).json()
    usd_price = response['ethereum']['usd']
    eur_price = response['ethereum']['eur']
    timestamp = datetime.now().strftime("%H:%M:%S")

    return (
        f" 💰 Current Ethereum Price:\n"
        f"\n"
        f" USD: ${usd_price}\n"
        f" EUR: €{eur_price}\n"
        f"\n"
        f"fetched at {timestamp}"
    )

# start command with basic explanation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ( 
        f"Hello I am GleppiesBot\n"
        f"(there are only are a few experimental commands atm)\n"
        f"Use /help to check all the available commands!"
    )
    await update.message.reply_text(message)

# help command with all the available commands
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        f"Current commands:\n"
        f"/start: basic information about the bot.\n"
        f"/btc: fetches the latest price of Bitcoin in Euro & USD.\n"
        f"/eth: fetches the latest price of Ethereum in Euro & USD.\n"
        f"/setbtcmessage: sets an automated message for bitcoin (2m,10m,30m,1h,1d).\n"
        f"/unset: cancels the automated BTC message."
    )
    await update.message.reply_text(message)

# /btc command handler
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = fetch_btc_price_message()
    await update.message.reply_text(message)

# /eth command handler 
async def eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = fetch_eth_price_message()
    await update.message.reply_text(message)

# Btc price to specific chat
def send_btc_update(chat_id):
    message = fetch_btc_price_message()
    bot = Bot(token=token)
    asyncio.run(bot.send_message(chat_id=chat_id, text=message))

# set btc automated message command 
async def set_btc_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id  = update.message.chat_id
    args = context.args

    # preventing an error
    if not args or args[0] not in ["2m","10m", "30m", "1h", "1d"]:
        await update.message.reply_text(
            "Command usage: \n\n/setbtcmessage [2m|10m|30m|1h|1d]\nExample: /setbtcmessage 1h"
        )
        return
    
    # remove previous job if it exists and new one started
    if chat_id in user_intervals:
        scheduler.remove_job(user_intervals[chat_id])

    # set interval for the command
    interval = args[0]
    job_id = f"btc_{chat_id}"

    if interval == "2m":
        scheduler.add_job(send_btc_update, 'interval', minutes=2, args=[chat_id], id=job_id)
    elif interval == "10m":
        scheduler.add_job(send_btc_update, 'interval', minutes=10, args=[chat_id], id=job_id)
    elif interval == "30m":
        scheduler.add_job(send_btc_update, 'interval', minutes=30, args=[chat_id], id=job_id)
    elif interval == "1h":
        scheduler.add_job(send_btc_update, 'interval', hours=1, args=[chat_id], id=job_id)
    elif interval == "1d":
        scheduler.add_job(send_btc_update, 'interval', days=1, args=[chat_id], id=job_id)

    user_intervals[chat_id] = job_id
    await update.message.reply_text(f"Btc updates scheduled every {interval}! \nTo remove use /unset")

# unset btc automated message command
async def unset_btc_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in user_intervals:
        scheduler.remove_job(user_intervals[chat_id])
        del user_intervals[chat_id]
        await update.message.reply_text("❌ BTC updates have been canceled.")
    else:
        await update.message.reply_text("⚠️ No BTC update schedule was set.")

# building the app
app = ApplicationBuilder().token(token).build()

# COMMAND HANDLERS

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
# currencies
app.add_handler(CommandHandler("btc", btc))
app.add_handler(CommandHandler("eth", eth))
# automated messages for currencies
app.add_handler(CommandHandler("setbtcmessage", set_btc_message))
app.add_handler(CommandHandler("unset", unset_btc_message))

# run the bot
app.run_polling()
