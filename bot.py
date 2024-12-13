import os
import logging
import discord
from discord.ext import commands
from config import TOKEN
from music import MusicSlash
from control_panel import ControlPanel
from logging_config import logger

# Configuration des intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

# Création du bot
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    """Charge les cogs de manière asynchrone."""
    try:
        await bot.add_cog(MusicSlash(bot))
        await bot.add_cog(ControlPanel(bot))
        logger.info("✅ Cogs chargés avec succès.")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement des cogs : {e}")

# Gestion des événements
@bot.event
async def on_ready():
    """Événement déclenché lorsque le bot est prêt."""
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ {len(synced)} commandes synchronisées : {[cmd.name for cmd in synced]}")
    except Exception as e:
        logger.error(f"❌ Erreur de synchronisation des commandes : {e}")
    logger.info(f"✅ Bot prêt en tant que {bot.user} (ID : {bot.user.id})")

@bot.event
async def on_disconnect():
    """Log la déconnexion du bot."""
    logger.warning("⚠️ Bot déconnecté. Vérifiez votre connexion ou hébergeur.")

@bot.event
async def on_resumed():
    """Log la reconnexion du bot."""
    logger.info("✅ Bot reconnecté avec succès.")

@bot.event
async def on_voice_state_update(member, before, after):
    """Supprime les fichiers musicaux lorsque le bot quitte un canal vocal."""
    if member == bot.user and before.channel and not after.channel:
        logger.info("🔊 Le bot a quitté un salon vocal. Nettoyage des fichiers musicaux...")
        music_dir = "music"
        if os.path.exists(music_dir):
            for file in os.listdir(music_dir):
                try:
                    os.remove(os.path.join(music_dir, file))
                    logger.info(f"✅ Fichier supprimé : {file}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la suppression de {file}: {e}")
        else:
            logger.warning("⚠️ Dossier 'music' introuvable.")

# Commandes Slash
@bot.tree.command(name="ping", description="Affiche la latence du bot.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latence : {latency} ms")
    logger.info(f"Commande /ping utilisée. Latence : {latency} ms")

@bot.tree.command(name="sync", description="Force la synchronisation des commandes slash.")
async def sync(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator:
        try:
            synced = await bot.tree.sync()
            await interaction.response.send_message(f"✅ {len(synced)} commandes synchronisées.", ephemeral=True)
            logger.info("✅ Synchronisation manuelle réussie.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur de synchronisation : {e}", ephemeral=True)
            logger.error(f"❌ Erreur de synchronisation manuelle : {e}")
    else:
        await interaction.response.send_message("❌ Vous n'avez pas les permissions requises.", ephemeral=True)

@bot.tree.command(name="debug", description="Effectue un test pour vérifier que le bot fonctionne.")
async def debug(interaction: discord.Interaction):
    try:
        await interaction.response.send_message("✅ Debug réussi. Tout fonctionne correctement !")
        logger.info("Commande /debug exécutée avec succès.")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution de /debug : {e}")
        await interaction.response.send_message(f"❌ Une erreur s'est produite : {e}")

@bot.event
async def on_command_error(ctx, error):
    """Gestion des erreurs de commandes."""
    logger.error(f"❌ Erreur détectée : {error}")
    await ctx.send(f"❌ Une erreur est survenue : {error}")

# Démarrage avec relance automatique en cas d'erreur
if __name__ == "__main__":
    import asyncio

    async def main():
        """Lance le bot et relance en cas de crash."""
        while True:
            try:
                logger.info("🚀 Démarrage du bot...")
                async with bot:
                    await bot.start(TOKEN)
            except Exception as e:
                logger.error(f"❌ Crash du bot : {e}")
                logger.info("🔄 Redémarrage dans 5 secondes...")
                await asyncio.sleep(5)

    asyncio.run(main())
