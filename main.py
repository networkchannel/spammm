import os
import sys

# Désactive les imports vocaux pour éviter les erreurs sur Render
sys.modules['audioop'] = None

import discord
import asyncio
from datetime import datetime, timezone
from flask import Flask
from threading import Thread

# 🚨 ATTENTION : TOKEN D'UTILISATEUR. À UTILISER UNIQUEMENT SI AUTORISATION EXPLICITE DE DISCORD.
TOKEN = os.environ.get("DISCORD_TOKEN")

# --- CONFIGURATION MULTI-SALONS ---
# La clé est l'ID du salon (int), la valeur est le cooldown (en secondes)
# 1m40s = 100s, 2m05s = 125s
CHANNELS_COOLDOWNS = {
    1400153729914638487: 100,  # Ton premier salon (1m40s)
    1416991351332933672: 125,  # Le deuxième salon (2m05s)
    1416991379908722769: 125,  # Le troisième salon (2m05s)
}
# -----------------------------------

MESSAGE = """\
# :rotating_light: NOUVEAU SCRIPT STEAL A BRAINROT GRATUIT
# :bangbang: IL TE PERMET D'ETRE INTOUCHABLE MEME SI TU AS UN BRAINROT DANS LES MAINS
# ⚡️ LE MEILLEUR EXISTANT EN PLUS ON VA FAIRE DES GIVEAWAY
# :warning: REJOINS NOUS LIEN EN BIO FRERO !!!
"""

# Dictionnaire pour stocker l'heure du dernier envoi pour chaque salon
last_sent_times = {}

# --- FLASK APP (pour Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>404 - Page non trouvée</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                font-size: 48px;
                margin: 0;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤷‍♂️</h1>
            <h1>Rien à voir ici</h1>
            <p>Cette page n'existe pas ou n'est pas accessible.</p>
        </div>
    </body>
    </html>
    """, 200

@app.route('/status')
def status():
    return {"status": "running", "channels": len(CHANNELS_COOLDOWNS)}, 200

def run_flask():
    """Lance Flask sur le port 10000 (Render par défaut)"""
    app.run(host='0.0.0.0', port=10000)
# -----------------------------------

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")
        
        # Lance une tâche asynchrone pour chaque salon
        for channel_id in CHANNELS_COOLDOWNS:
            self.loop.create_task(self.send_message_periodically(channel_id))
        
        print(f"🚀 Tâches d'envoi lancées pour {len(CHANNELS_COOLDOWNS)} salons avec leurs cooldowns respectifs.")

    async def get_last_sent_time(self, channel):
        """Recherche l'heure du dernier message de cet utilisateur dans le salon."""
        # Limite la recherche à 50 messages
        async for msg in channel.history(limit=50):
            # C'est ici qu'on vérifie si l'auteur est l'utilisateur connecté (self-bot)
            if msg.author == self.user:
                return msg.created_at.replace(tzinfo=timezone.utc).timestamp()
        return None

    async def send_message_periodically(self, channel_id: int):
        """Gère l'envoi et le cooldown pour un seul salon, de manière indépendante."""
        
        channel = self.get_channel(channel_id)
        cooldown = CHANNELS_COOLDOWNS.get(channel_id, 0)
        
        if channel is None:
            print(f"❌ Salon {channel_id} introuvable ! Tâche arrêtée.")
            return

        print(f"⚙️ Tâche lancée pour le salon {channel.name} ({channel_id}) avec un cooldown de {cooldown}s.")

        # Vérification initiale pour reprendre le cycle après un redémarrage
        last_time = await self.get_last_sent_time(channel)
        if last_time:
            last_sent_times[channel_id] = last_time
            print(f"⏳ Dernier message trouvé dans {channel.name} à {datetime.fromtimestamp(last_time)}")

        while True:
            try:
                now = datetime.now(timezone.utc).timestamp()
                
                # Récupère le dernier temps d'envoi pour ce salon
                last_time = last_sent_times.get(channel_id, 0) 
                
                # Calcul du temps écoulé et du temps d'attente nécessaire
                elapsed = now - last_time
                wait_time = max(0, cooldown - elapsed)
                
                if wait_time > 0:
                    print(f"⏱ Salon {channel.name} : Cooldown actif, attente de {wait_time:.1f} secondes...")
                    # Attendre le temps restant
                    await asyncio.sleep(wait_time)

                # Envoi du message une fois le cooldown terminé
                await channel.send(MESSAGE)
                # Met à jour le temps du dernier envoi pour ce salon uniquement
                last_sent_times[channel_id] = datetime.now(timezone.utc).timestamp()
                print(f"📨 Message envoyé dans {channel.name} !")

                # Attendre le COOLDOWN complet (plus une seconde) avant la prochaine vérification
                await asyncio.sleep(cooldown + 1) 

            except Exception as e:
                print(f"⚠️ Erreur dans la boucle du salon {channel_id}: {e}")
                # En cas d'erreur, attendre 30 secondes avant de réessayer
                await asyncio.sleep(30)


# Lance Flask dans un thread séparé
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

print("🌐 Serveur Flask démarré sur le port 10000")

# Lance le bot Discord
client = MyClient()
client.run(TOKEN)
