import discord
import traceback
from logging_config import logger  # Assure-toi d'avoir configuré le logger

async def report_error(bot, channel_id, error_message):
    """Envoie une notification d'erreur dans un canal Discord."""
    try:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(f"⚠️ **Erreur détectée :**\n```{error_message}```")
    except Exception as e:
        logger.error(f"❌ Impossible d'envoyer l'erreur : {e}")

async def global_error_handler(bot, event, *args, **kwargs):
    """Capture toutes les erreurs globales."""
    error_message = traceback.format_exc()
    logger.error(error_message)
    await report_error(bot, 123456789012345678, error_message)  # Remplace par l'ID du canal
