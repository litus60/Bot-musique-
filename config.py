from dotenv import load_dotenv
import os

# Charger le fichier .env
load_dotenv()

# Récupérer le Token depuis .env
TOKEN = os.getenv('DISCORD_TOKEN')

# Vérification du Token
if not TOKEN:
    raise ValueError("❌ Le token Discord n'a pas été trouvé. Assurez-vous que le fichier .env contient DISCORD_TOKEN.")
