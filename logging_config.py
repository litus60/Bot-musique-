import logging

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,  # Niveau minimum de log (INFO, DEBUG, WARNING, ERROR)
    format="%(asctime)s [%(levelname)s]: %(message)s",  # Format des logs
    datefmt="%Y-%m-%d %H:%M:%S",  # Format de l'horodatage
    filename="bot.log",  # Optionnel : écrit les logs dans un fichier au lieu de la console
    filemode="a"  # "a" pour ajouter au fichier existant, "w" pour écraser
)

# Crée un logger spécifique pour ton bot
logger = logging.getLogger("discord-bot")
