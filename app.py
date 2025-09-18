import os
from dotenv import load_dotenv
from pyairtable import Table, Api
from pyairtable.formulas import match
import requests
import random
import asyncio
import time
import schedule, time
from datetime import datetime, timezone
from quart import Quart, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")
TELEGRAM_WEBHOOK = os.getenv("TELEGRAM_WEBHOOK")

# === QUART APP ===
app = Quart(__name__)

def messaggio_telegram(result, channel_id, immagine):
   print("✅ Pubblicazione Offerta in corso..")
   print(immagine)
   try:
      headers= {"content-type": "application/json"}
      data = {
    "chat_id": channel_id,
    "photo": "https://cdn.studenti.stbm.it/images/2020/01/21/contabile-e-commercialista-orig.jpeg",  # URL dell'immagine
    "caption": f"""
    *NUOVA OFFERTA DI LAVORO*

*Azienda*:
{result['company']['display_name']}

*Dove*:
{result['location']['display_name']}

*Descrizione*:
{result['description']}
    """,  # Testo sotto la foto
    "parse_mode": "Markdown",
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "Candidati Ora",
                "url": result['redirect_url']
            }
        ]]
    }
}
      try:
          response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendPhoto", headers=headers, json=data).json()
          #print(response)
          print("✅ Messaggio inviato correttamente su Telegram!")
      except Exception as e:
          print(f"Errore invio messaggio su telegram: {e}")
   except Exception as e:
      print(f"Errore ricezione dettagli ad: {e}")

def trova_offerta(channel_id, Adzuna_Tag, channel_name):
  channel_id = f'{channel_id}'
  print(f"Cerco offerta per {channel_name}")
  url_adzuna = f"http://api.adzuna.com/v1/api/jobs/it/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_API_KEY}&results_per_page=1&category={Adzuna_Tag}&sort_by=date" #f"https://api.adzuna.com/v1/api/jobs/es/search/1?app_id=ba0b720b&app_key={ADZUNA_API_KEY}&results_per_page=1&what={ruolo_ricercato}&where=ibiza&sort_by=date"
  try :
    response = requests.get(url_adzuna).json()
    result = response['results'][0]
    #print(result)
    api = Api(AIRTABLE_API_KEY)
    TABLE_NAME = "Offerte"
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)
    try:
      adzuna_id_check = table.all(formula=f"{{adzuna_id}}='{response['results'][0]['id']}'")
      if adzuna_id_check == 1:#**
        print(f"⚠️ ID ({response['results'][0]['id']}) già presente")
      else:
        immagine = random.choice(["https://i.postimg.cc/59w4NPPL/Vlog-Titolo-Thumbnail-You-Tube.png", "https://i.postimg.cc/nhLp2nnG/Vlog-Titolo-Thumbnail-You-Tube-2.png", "https://i.postimg.cc/GhdcBkNN/Vlog-Titolo-Thumbnail-You-Tube-1.png"])
        try:
          new_record = table.create({"title": f"{result['title']}", "latitude": f"{result['latitude']}", "longitude": f"{result['longitude']}", "company": f"{result['company']['display_name']}", "adzuna_id": f"{result['id']}", "location": f"{result['location']['display_name']}", "description": f"{result['description']}", "redirect_url": f"{result['redirect_url']}", "immagine": immagine})
          print("✅ Nuovo record creato:", new_record)
          messaggio_telegram(result, channel_id, immagine)
        except Exception as e:
          print(f"Errore in creazione row nel database: {e}")
    except Exception as e:
      print(f"Errore nel fetching info sull'id dell'offerta: {e}")
  except Exception as e:
    print(f"Errore in Cerco Offerta: {e}")

def schedula_annuncio_mensile():
  #prendere dati da airtable per canali, for each messaggio telegram**
  if datetime.now(timezone.utc).day == 1:
    headers= {"content-type": "application/json"}
    data = {
    "chat_id": 'PROVA',
    "photo": "https://cdn.studenti.stbm.it/images/2020/01/21/contabile-e-commercialista-orig.jpeg",  # URL dell'immagine
    "caption": f"""
    *OFFERTA TEAMTIME*
    """,
    "parse_mode": "Markdown",
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "MODIFICA",
                "url": 'URL'
            }]]}}
    try:
      response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendPhoto", headers=headers, json=data).json()
      print("✅ Messaggio inviato correttamente su Telegram!")
    except Exception as e:
      print(f"Errore invio messaggio su telegram: {e}")

def start_bot():
   print("Start..")
   time.sleep(5)
   api = Api(AIRTABLE_API_KEY)
   TABLE_NAME = "Canali"
   table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)
   records = table.all()
   for record in records:
      trova_offerta(record['fields']['Channel_ID'], record['fields']['Adzuna_Tag'], record['fields']['Nome'])
      time.sleep(2)

#start_bot()

print("🕐 Server", datetime.now(timezone.utc).isoformat())
schedule.every().day.at("17:47:00").do(start_bot)
#schedule.every().day.at("12:00:00").do(start_bot)
#schedule.every().day.at("18:00:00").do(start_bot)
#schedule.every().day.at("13:00").do(schedula_annuncio_mensile)

# === TELEGRAM APP ===
telegram_app = Application.builder().token(TELEGRAM_BOT_KEY).build()


async def start(update: Update, context: CallbackContext):
    chat_type = update.effective_chat.type
    print(">> Ricevuto /start da %s", update.effective_user.username)
    if chat_type != "private":
      await update.message.reply_text("❌ Questo comando funziona solo in chat privata. Scrivimi qui 👉 ")
      return


async def scheduler_loop():
    while True:
        schedule.run_pending()
        await asyncio.sleep(10)
        print("Waiting for action..")


# Inizializza il bot
#telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(CommandHandler("start", start))
#telegram_app.add_handler(CommandHandler("chatid", log_chat_id))

@app.route("/", methods=["GET","POST"])
async def home():
    return "ok"

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = await request.get_json()
        print("Webhook data:", data)   
        update = Update.de_json(data, telegram_app.bot)
        print("Webhook update:", update) 
        await telegram_app.process_update(update)
        return "OK", 200
    except Exception as e:
        print(f"Errore nel webhook: {e}")
        return "Errore interno", 500

@app.before_serving
async def startup():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(TELEGRAM_WEBHOOK)
    asyncio.create_task(scheduler_loop())

