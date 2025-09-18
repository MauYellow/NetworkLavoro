import logging
import asyncio

import random
import schedule, time
from datetime import datetime, timezone

#da sopra non servono

import os
from dotenv import load_dotenv
import pyairtable
import requests
from quart import Quart, request
from telegram import Update
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")
AIRTABLE_URL = os.getenv("AIRTABLE_URL")
TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


AIRTABLE_TOKEN = "a"
AIRTABLE_URL = "a"


def trova_offerta():
  url_adzuna = f"http://api.adzuna.com/v1/api/jobs/gb/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_API_KEY}&results_per_page=20&what=javascript%20developer&content-type=application/json" #f"https://api.adzuna.com/v1/api/jobs/es/search/1?app_id=ba0b720b&app_key={ADZUNA_API_KEY}&results_per_page=1&what={ruolo_ricercato}&where=ibiza&sort_by=date"
  response = requests.get(url_adzuna).json()
  print(response)


# Configurazioni

#CHANNEL_USERNAME = "@amazon_hunter_italia"
#CHANNEL_BARTENDER = "-1001213886944" # Trader Chat > "-4752969963" # The bartender group > "-1001213886944"
#ADMIN_ID = "975722590"



# Memorizza le offerte
lista_offerte = []

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === QUART APP ===
app = Quart(__name__)

@app.route("/dati-mappa")
async def dati_mappa():
    try:
        response = requests.get(AIRTABLE_URL, headers=HEADERS).json()
        markers = []
        for record in response.get("records", []):
            fields = record.get("fields", {})
            lat = fields.get("Latitude")
            lon = fields.get("Longitude")
            if lat and lon:
                markers.append({
                    "lat": lat,
                    "lon": lon,
                    "titolo": fields.get("Nome della struttura", "N/A"),
                    "zona": fields.get("Zona", "N/A"),
                    "ruolo": fields.get("Figura ricercata", "N/A"),
                    "link": "https://t.me/BartenderApp_Bot?start=start",
                    "foto": fields.get("Foto")
                })
        return {"markers": markers}
    except Exception as e:
        print(f"Errore caricamento mappa: {e}")
        return {"markers": []}

@app.route("/mappa-offerte")
async def mappa_offerte():
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Mappa Offerte Lavoro</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
  <style>
    #map { height: 100vh; }
    .popup-img {
      width: 100px;
      height: 100px;
      object-fit: cover;
      border-radius: 8px;
      margin-top: 8px;
    }
  </style>
</head>
<body>
<div id="map"></div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
  const map = L.map('map').setView([41.9028, 12.4964], 4);  // Centra su Europa, zoom 4

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  fetch('/dati-mappa')
    .then(res => res.json())
    .then(data => {
      data.markers.forEach(m => {
        const icon = L.icon({
          iconUrl: 'https://img.icons8.com/office/40/marker.png',
          iconSize: [25, 25]
        });

        const popupContent = `
          <b>${m.ruolo}</b><br>
          ${m.titolo}<br>
          ${m.zona}<br>
          <a href="${m.link}" target="_blank">Apply Now</a><br>
          <img src="${m.foto}" class="popup-img" alt="Offerta">
        `;

        L.marker([m.lat, m.lon], { icon: icon }).addTo(map)
          .bindPopup(popupContent);
      });
    });
</script>
</body>
</html>
"""


def trova_offerte():
    print("Ricerca offerta")
    ruolo_ricercato = random.choice(["bartender&title_only=bartender", "bar%20manager&title_only=bar%20manager"])
    print(ruolo_ricercato)
    ibiza = random.choice([1, 2, 3, 4]) #deve tornare con 1
    if ibiza == 1:
       print("Ricerca in Ibiza..")
       url_adzuna = f"https://api.adzuna.com/v1/api/jobs/es/search/1?app_id=ba0b720b&app_key=e9122a6c620df77f0249840c4a6e8570&results_per_page=1&what={ruolo_ricercato}&where=ibiza&sort_by=date"
    else:
       print("Ricerca resto nel mondo..")
       zona_ricercata = random.choice(["ch", "es", "fr", "gb", "it", "it", "it"]) #tolto us perché Adzuna dice "job non available nella mia regione"
       url_adzuna = f"https://api.adzuna.com/v1/api/jobs/{zona_ricercata}/search/1?app_id=ba0b720b&app_key=e9122a6c620df77f0249840c4a6e8570&results_per_page=1&what={ruolo_ricercato}&sort_by=date"
       print(zona_ricercata)

    try:
        response = requests.get(url_adzuna).json()
        print(response)
        results = response['results'][0]
        salary_min = results.get('salary_min')
        salary_max = results.get('salary_max')
        if salary_min and salary_max:
          paga = f"{salary_min}€ - {salary_max}€"
        else:
          paga = "N/A"
        if "manager" in ruolo_ricercato:
          ruolo = "Bar Manager"
        else:
          ruolo = "Bartender"
        print(f"✅ Job offer {results['id']} retrieved dorrectly, checking if already in Airtable..!")
        headers = {
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        }
        response = requests.get("https://api.airtable.com/v0/app371e6RlBMnvOa0/Bartender_Annunci?maxRecords=55&view=Grid%20view&fields%5B%5D=Id%20Adzuna%20API", headers=headers).json()
        airtable_ids = [
          record['fields'].get('Id Adzuna API')
          for record in response['records']
          if 'Id Adzuna API' in record['fields']
          ]
        
        print(f"Airtable_Ids: {airtable_ids}")

        if int(results['id']) in airtable_ids:
          print("🔁 Già presente")
        else:
          print("✅ Offerta non presente in lista, cancellazione ultima offerta in corso..")
          totale_righe = len(response['records']) - 1
          print(f"Totale righe: {totale_righe}")
          riga_da_eliminare = response['records'][totale_righe]['id']
          print(f"Riga da eliminare: {riga_da_eliminare}")
          headers = {
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        }
          try:
             response_delete = requests.delete(f"https://api.airtable.com/v0/app371e6RlBMnvOa0/Bartender_Annunci/{riga_da_eliminare}",headers=headers).json()
             print(f"Risposta cancellazione Airtable {response_delete}")
          except Exception as e:
             print(f"Errore eliminazione riga: {e}")

          print("✅ Aggiungo l'offerta ad Airtable..")
          if "manager" in ruolo.lower():
            foto_url = "https://img.icons8.com/bubbles/100/manager.png"
          else:
            foto_url = "https://img.icons8.com/bubbles/100/cocktail.png"
          headers = {
            "Authorization": f"Bearer {AIRTABLE_TOKEN}",
            "Content-type": "application/json"
        }
          
          data = {
            "records": [
                {
                "fields": {
                    "Nome della struttura": f"{results['title']}",
                    "Zona": f"{results['location']['display_name']}",
                    "Figura ricercata": ruolo,
                    "Giorno di inizio": "As soon as possible",
                    "Tipo di offerta": ["Contratto"],
                    "Orario di lavoro": "Full Time",
                    "Paga": f"{paga}",
                    "Mail dove ricevere i curriculum dei candidati": f"{results['redirect_url']}",
                    "Note": f"{results['description']}",
                    "Views": 0,
                    "Click": 0,
                    "Foto": foto_url,
                    "Id Adzuna API": int(results['id']),
                    "Click Telegram": 0,
                    "Latitude": str(results.get('latitude', "0.0")),
                    "Longitude": str(results.get('longitude', "0.0"))
                }
                }
            ]
        }
          try:
            response = requests.post("https://api.airtable.com/v0/app371e6RlBMnvOa0/Bartender_Annunci", headers=headers, json=data).json()
            print(response)
            print("✅ Aggiunta l'offerta ad Airtable!")
            # Wage block
            if paga != "N/A":
              wage_block = f"*Net Wage*:\n{paga}\n"
            else:
              wage_block = ""

            # Location tip (Ibiza)
            location_tip = "🏖️🍸🪩\nPrima di considerare I'offerta, leggi la guida: [Lavorare ad Ibiza](https://www.mauriziopolverini.com/post/guida-al-lavoro-lavorare-come-bartender-a-ibiza) , per documenti, alloggi, stipendio e molto altro." if "ibiza" in results['location']['display_name'].lower() else ""

            # Manager tip
            manager_tip = "📊🍸📈\nPer questo ruolo potrebbe esserti utile una competenza base di Excel: Inizia con [il primo video gratis](https://maurizio-polverini-s-school.teachable.com/courses/corso-base-avanzato-excel-per-bar-manager/lectures/51974302)" if "manager" in ruolo.lower() else ""
            
            text = f"""
🍸 *NEW JOB OFFER*

*Role*: {ruolo}
*Where*: {results['location']['display_name']}
{wage_block}
{location_tip}{manager_tip}

🔽 To get more information and apply, CLICK HERE 🔽"""

            headers= {
               "content-type": "application/json",
            }
            data = {
                "chat_id": CHANNEL_BARTENDER,
                "parse_mode": "Markdown",
                "text": text,
                "disable_web_page_preview": "true",
                "reply_markup": {
                   "inline_keyboard": [[
                      {
                         "text": "🗺️ Explore Map",
                         "url": "https://zoophagous-lisbeth-app-eleven-758c0d6d.koyeb.app/mappa-offerte"
                      },
                      {
                    "text": "📨 Apply Now",
                    "url": "https://t.me/BartenderApp_Bot?start=apply"
                   }
                   ]]
            
            }
            }
            try:
                response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage", headers=headers, json=data).json()
                print("✅ Messaggio inviato correttamente su Telegram!")
            except Exception as e:
                print(f"Errore Invio su Telegram: {e}")

          except Exception as e:
            print(f"Errore: {e}")
            
    except Exception as e:
        print(f"Error: {e}")


def pubblica_ads():
   print("✅ Pubblicazione Ad in corso..")
   headers = {
      "Authorization": f"Bearer {AIRTABLE_TOKEN}"
   }
   try:
      response = requests.get("https://api.airtable.com/v0/app371e6RlBMnvOa0/AdsTelegramPythonBot?maxRecords=3&view=Grid%20view", headers=headers).json()
      print("✅ Offerta collezionata correttamente, invio nel canale in corso..")
      ad = response['records'][0]['fields']
      headers= {
               "content-type": "application/json",
            }
      data = {
    "chat_id": CHANNEL_BARTENDER,
    "photo": ad["Image"],  # URL dell'immagine
    "caption": ad["Text"],  # Testo sotto la foto
    "parse_mode": "Markdown",
    "reply_markup": {
        "inline_keyboard": [[
            {
                "text": "Offerta a tempo su Amazon!",
                "url": ad["URL"]
            }
        ]]
    }
}
      try:
          response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendPhoto", headers=headers, json=data).json()
          print("✅ Messaggio inviato correttamente su Telegram!")
      except Exception as e:
          print(f"Errore invio messaggio su telegram: {e}")
   except Exception as e:
      print(f"Errore ricezione dettagli ad: {e}")

def schedula_annuncio_mensile():
    if datetime.now(timezone.utc).day == 1:
        print("🗓️ È il 1 del mese! Lancio pubblica_ad()")
        pubblica_ads()

print("🕐 Server", datetime.now(timezone.utc).isoformat())
#schedule.every().day.at("08:00:00").do(trova_offerte)
#schedule.every().day.at("12:00:00").do(trova_offerte)
#schedule.every().day.at("18:00:00").do(trova_offerte)
#schedule.every().day.at("13:00").do(schedula_annuncio_mensile)

# === TELEGRAM APP ===
telegram_app = Application.builder().token(TELEGRAM_BOT_KEY).build()

# === HANDLER ===
async def start(update: Update, context: CallbackContext):
    chat_type = update.effective_chat.type
    logging.info(">> Ricevuto /start da %s", update.effective_user.username)
    if chat_type != "private":
       await update.message.reply_text("❌ Questo comando funziona solo in chat privata. Scrivimi qui 👉 [@BartenderApp_Bot](https://t.me/BartenderApp_Bot?start=start)", parse_mode="Markdown")
       return
    else:
       await update.message.reply_text("🔄 Loading best offers...")
    # Recupera i dati da Airtable
       response = requests.get(AIRTABLE_URL, headers=HEADERS).json()
       lista_offerte.clear()  # Pulisce la lista prima di riempirla di nuovo

       for offer in response.get("records", []):
           fields = offer.get("fields", {})
           if "www" in fields.get("Mail dove ricevere i curriculum dei candidati", ""):
               lista_offerte.append({
                "record_id": offer.get("id"),
                "Figura ricercata": fields.get("Figura ricercata", "N/A"),
                "Zona": fields.get("Zona", "N/A"),
                "Link": fields.get("Mail dove ricevere i curriculum dei candidati", "#"),
            })

       if not lista_offerte:
           await update.message.reply_text("❌ No job offers available at the moment.")
           return

    # Crea i pulsanti delle offerte
       keyboard = [[InlineKeyboardButton(f"{offer['Figura ricercata']}, {offer['Zona']}", callback_data=offer["record_id"])] 
                   for offer in lista_offerte]
       reply_markup = InlineKeyboardMarkup(keyboard)

       await update.message.reply_text("""🍸 Selected Job Offers List:""", reply_markup=reply_markup)

async def check_subscription(user_id: int, context: CallbackContext) -> bool:
    """Controlla se l'utente è iscritto a entrambi i canali"""
    try:
        member_amazon = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        member_bartender = await context.bot.get_chat_member(CHANNEL_BARTENDER, user_id)

        is_amazon = member_amazon.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
        is_bartender = member_bartender.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]

        return is_amazon and is_bartender

    except Exception as e:
        print(f"⚠️ Errore controllo iscrizione: {e}")
        return False

async def log_chat_id(update: Update, context: CallbackContext):
    chat = update.effective_chat
    print(f"🆔 chat_id: {chat.id}, tipo: {chat.type}, titolo: {chat.title}")
    await update.message.reply_text(f"✅ chat_id: `{chat.id}`", parse_mode="Markdown")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or "Senza username"
    record_id = query.data
    print(f"📌 Record ID ricevuto: {record_id}")

    # Recupera i dettagli dell'offerta da Airtable
    airtable_url = f"https://api.airtable.com/v0/app371e6RlBMnvOa0/Bartender_Annunci/{record_id}"
    try:
        response = requests.get(airtable_url, headers=HEADERS).json()
        fields = response.get("fields", {})

        figura = fields.get("Figura ricercata", "N/A")
        zona = fields.get("Zona", "N/A")
        link_or_mail = fields.get("Mail dove ricevere i curriculum dei candidati", "#")

        # Notifica all’admin
        message = f"👤 {username} (ID: {user_id}) ha selezionato: {figura} in {zona}"
        await context.bot.send_message(ADMIN_ID, message)

        # Verifica iscrizione
        if await check_subscription(user_id, context):
            # Invia bottone per candidarsi
            keyboard = [[InlineKeyboardButton("✅ Apply now!", url=link_or_mail)]]
            await query.message.reply_text(
                f"✅ You can apply for:\n{figura} in {zona}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # 📈 Aggiorna Click Telegram
            current_clicks = fields.get("Click Telegram", 0)
            update_data = {
                "fields": {
                    "Click Telegram": current_clicks + 1
                }
            }
            requests.patch(
                airtable_url,
                headers={**HEADERS, "Content-Type": "application/json"},
                json=update_data
            )
        else:
            # Verifica stato iscrizione per entrambi i canali
          is_amazon = False
          is_bartender = False

          try:
            member_amazon = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
            is_amazon = member_amazon.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
          except:
            pass

          try:
            member_bartender = await context.bot.get_chat_member(CHANNEL_BARTENDER, user_id)
            is_bartender = member_bartender.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
          except:
            pass

# Crea simbolo accanto al nome
          status_amazon = "✅" if is_amazon else "👉"
          status_bartender = "✅" if is_bartender else "👉"

# Messaggio di richiesta iscrizione
          await query.message.reply_text(
            """🇮🇹 Per procedere unisciti a questi canali:\n\n🇬🇧 To proceed, please join all of these channels:\n\n 🇪🇸 Para continuar, únete a todos estos canales:\n""",
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
    [InlineKeyboardButton(f"{status_amazon} Join Amazon Group -70%", url=CHANNEL_USERNAME.replace("@", "https://t.me/"))],
    [InlineKeyboardButton(f"{status_bartender} Join Bartender Group", url="https://t.me/The_Bartender_Group")],
    [InlineKeyboardButton("✉️ Continue", callback_data=record_id)]
    ]))

    except Exception as e:
        print(f"❌ Errore nel recupero o aggiornamento Airtable: {e}")
        await query.message.reply_text("❌ Si è verificato un errore. Riprova più tardi.")

    await query.answer()


# Inizializza il bot
#telegram_app.add_handler(CallbackQueryHandler(button_handler))
#telegram_app.add_handler(CommandHandler("start", start))
#telegram_app.add_handler(CommandHandler("chatid", log_chat_id))


# === WEBHOOK ===
@app.route("/")
async def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        data = await request.get_json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return "OK", 200
    except Exception:
        logging.exception("Errore nel webhook:")
        return "Errore interno", 500

async def scheduler_loop():
    while True:
        schedule.run_pending()
        await asyncio.sleep(30)
        print("Waiting for action..")

# === AVVIO APP ===
if __name__ == "__main__":
    async def main():
        await telegram_app.initialize()
        await telegram_app.start()
        try:
          await telegram_app.bot.set_webhook(WEBHOOK_URL)
          logging.info(f"✅ Webhook impostato su: {WEBHOOK_URL}")
          asyncio.create_task(scheduler_loop())
        except Exception as e:
          print(f"Errore: {e}")

        port = int(os.environ.get("PORT", 8000))
        await app.run_task(host="0.0.0.0", port=port)

    asyncio.run(main())




