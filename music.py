import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio

# Configuration du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("MusicSlash")


class MusicSlash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []  # File d'attente des musiques
        self.voice_client = None  # Référence au client vocal actuel
        self.is_playing = False

        if not os.path.exists("music"):
            os.makedirs("music")

    def cleanup_audio_files(self):
        """Supprime les fichiers audio téléchargés."""
        folder = "music"
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    logger.info(f"✅ Fichier supprimé : {file_path}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la suppression de {file_path}: {e}")

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Vérifie si l'URL est valide."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and "youtube.com" in parsed.netloc

    async def play_next(self):
        """Lit la musique suivante dans la file d'attente."""
        if self.queue:
            url, interaction = self.queue.pop(0)
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                    'outtmpl': 'music/%(title)s.%(ext)s',
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = f"music/{info['title']}.mp3"

                logger.info(f"🎶 Lecture de : {info['title']}")
                self.is_playing = True
                self.voice_client.play(
                    discord.FFmpegPCMAudio(file_path),
                    after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                )
                await interaction.followup.send(f"🎶 En cours : {info['title']}")
            except Exception as e:
                logger.error(f"❌ Erreur : {e}")
                await interaction.followup.send("❌ Impossible de lire la musique.")
                self.is_playing = False
        else:
            self.is_playing = False
            logger.info("🎵 Fin de la playlist.")

    async def play_music_from_panel(self, interaction: discord.Interaction, url: str):
        """Ajoute une musique depuis le panneau interactif."""
        try:
            if not self.is_valid_url(url):
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Lien YouTube invalide.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Lien YouTube invalide.", ephemeral=True)
                return

            if not self.voice_client or not self.voice_client.is_connected():
                if interaction.user.voice:
                    self.voice_client = await interaction.user.voice.channel.connect()
                else:
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Vous devez être dans un canal vocal.", ephemeral=True)
                    else:
                        await interaction.followup.send("❌ Vous devez être dans un canal vocal.", ephemeral=True)
                    return

            self.queue.append((url, interaction))
            if not interaction.response.is_done():
                await interaction.response.send_message(f"🎵 Musique ajoutée : {url}", ephemeral=True)
            else:
                await interaction.followup.send(f"🎵 Musique ajoutée : {url}", ephemeral=True)

            if not self.is_playing:
                self.is_playing = True
                await self.play_next()

        except Exception as e:
            logger.error(f"❌ Erreur ajout de musique depuis le panneau : {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)

    async def skip_music(self, interaction: discord.Interaction):
        """Passe à la musique suivante."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await interaction.response.send_message("⏭ Musique suivante...", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Aucune musique en cours de lecture.", ephemeral=True)

    async def stop_music(self, interaction: discord.Interaction):
        """Arrête la lecture."""
        if self.voice_client:
            self.voice_client.stop()
            self.queue.clear()
            self.is_playing = False
            await interaction.response.send_message("🛑 Musique arrêtée et file d'attente vidée.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Le bot n'est pas connecté à un canal vocal.", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Nettoyage des fichiers lors de la déconnexion vocale."""
        if member == self.bot.user and before.channel and not after.channel:
            logger.info("👋 Le bot a quitté le vocal. Nettoyage des fichiers...")
            self.cleanup_audio_files()
            self.queue.clear()
            self.is_playing = False

    @app_commands.command(name="play", description="Joue une musique depuis un lien YouTube.")
    async def play(self, interaction: discord.Interaction, url: str):
        """Ajoute une musique à la file d'attente."""
        await self.play_music_from_panel(interaction, url)

    @app_commands.command(name="skip", description="Passe à la musique suivante.")
    async def skip(self, interaction: discord.Interaction):
        """Passe à la musique suivante."""
        await self.skip_music(interaction)

    @app_commands.command(name="stop", description="Arrête la musique et vide la file d'attente.")
    async def stop(self, interaction: discord.Interaction):
        """Arrête la musique."""
        await self.stop_music(interaction)

    @app_commands.command(name="quitte", description="Déconnecte le bot et nettoie les fichiers.")
    async def quitte(self, interaction: discord.Interaction):
        if self.voice_client:
            await self.voice_client.disconnect()
            self.cleanup_audio_files()
            self.queue.clear()
            self.is_playing = False
            await interaction.response.send_message("👋 Déconnexion réussie.")
        else:
            await interaction.response.send_message("❌ Le bot n'est pas connecté.")


async def setup(bot):
    """Ajoute le cog MusicSlash au bot."""
    try:
        await bot.add_cog(MusicSlash(bot))
        logger.info("✅ Cog MusicSlash chargé avec succès.")
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du cog : {e}")
