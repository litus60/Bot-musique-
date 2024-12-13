import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

PANEL_DATA_FILE = "panel_data.txt"  # Fichier pour stocker les informations du panneau

# Configuration du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("ControlPanel")


class ControlPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_panel(self, channel: discord.TextChannel):
        """Créer un panneau interactif dans le canal spécifié."""
        embed = discord.Embed(
            title="🎵 Panneau de Contrôle du Bot Musical 🎵",
            description="Utilisez les boutons ci-dessous pour contrôler la lecture.",
            color=discord.Color.red()
        )
        embed.set_image(url="https://i.pinimg.com/originals/53/b6/d9/53b6d9653a81e060a4c91a2b6c548dfd.gif")
        embed.set_footer(text="Bot Musical - Contrôlez votre musique avec style!")

        message = await channel.send(embed=embed, view=self.MusicControlView(self.bot))
        with open(PANEL_DATA_FILE, "w") as f:
            f.write(f"{channel.id}\n{message.id}")
        logger.info(f"✅ Nouveau panneau créé dans le canal {channel.name}.")

    async def load_panel(self):
        """Charge le panneau existant à partir des données enregistrées."""
        try:
            with open(PANEL_DATA_FILE, "r") as f:
                channel_id, message_id = map(int, f.readlines())

            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning("❌ Canal introuvable. Le panneau ne peut pas être chargé.")
                return

            message = await channel.fetch_message(message_id)
            await message.edit(view=self.MusicControlView(self.bot))
            logger.info(f"✅ Panneau rechargé dans le canal {channel.name}.")
        except (FileNotFoundError, ValueError, discord.NotFound):
            logger.warning("❌ Aucun panneau existant trouvé ou données invalides.")

    class PlayMusicModal(discord.ui.Modal):
        """Formulaire pour ajouter un lien de musique."""
        def __init__(self, bot: commands.Bot):
            super().__init__(title="🎵 Ajouter une musique")
            self.bot = bot
            self.url_input = discord.ui.TextInput(
                label="Lien YouTube",
                placeholder="Entrez le lien YouTube ici...",
                style=discord.TextStyle.short
            )
            self.add_item(self.url_input)

        async def on_submit(self, interaction: discord.Interaction):
            """Action après soumission du formulaire."""
            url = self.url_input.value
            music_cog = self.bot.get_cog("MusicSlash")

            if music_cog and music_cog.is_valid_url(url):
                await interaction.response.defer()
                await music_cog.play_music_from_panel(interaction, url)
            else:
                await interaction.response.send_message("❌ Lien invalide. Veuillez fournir un lien YouTube valide.", ephemeral=True)

    class MusicControlView(discord.ui.View):
        """Vue interactive pour les boutons de contrôle musical."""
        def __init__(self, bot):
            super().__init__(timeout=None)
            self.bot = bot

        @discord.ui.button(label="▶️ Play", style=discord.ButtonStyle.green)
        async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Ouvre un formulaire pour entrer un lien YouTube."""
            await interaction.response.send_modal(ControlPanel.PlayMusicModal(self.bot))

        @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.blurple)
        async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()
                await interaction.response.send_message("⏸ Musique mise en pause.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Aucune musique en cours de lecture.", ephemeral=True)

        @discord.ui.button(label="⏯️ Reprendre", style=discord.ButtonStyle.blurple)
        async def reprendre_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
                interaction.guild.voice_client.resume()
                await interaction.response.send_message("▶️ Musique reprise.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Aucune musique en pause.", ephemeral=True)

        @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red)
        async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            music_cog = self.bot.get_cog("MusicSlash")
            if music_cog:
                await music_cog.stop(interaction)
            else:
                await interaction.response.send_message("❌ Le cog MusicSlash n'est pas chargé.", ephemeral=True)

        @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.blurple)
        async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Passe à la musique suivante via le bouton Skip."""
            music_cog = self.bot.get_cog("MusicSlash")
            if music_cog and hasattr(music_cog, "skip_music"):
                await music_cog.skip_music(interaction)
            else:
                await interaction.response.send_message("❌ Le cog MusicSlash n'est pas chargé ou incomplet.", ephemeral=True)

    @app_commands.command(name="setup", description="Configurer le panneau de contrôle dans un canal.")
    async def setup(self, interaction: discord.Interaction):
        """Configurer le panneau interactif dans un canal spécifique."""
        await interaction.response.send_message(
            "Veuillez mentionner le canal où le panneau doit être configuré (ex. : `#général`).", ephemeral=True
        )

        def check(msg: discord.Message):
            return (
                msg.author == interaction.user
                and msg.channel == interaction.channel
                and msg.content.startswith("<#")
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            channel_id = int(msg.content.strip("<>#"))
            channel = self.bot.get_channel(channel_id)

            if not channel or not isinstance(channel, discord.TextChannel):
                await interaction.followup.send("❌ Le canal spécifié est invalide.", ephemeral=True)
                return

            await self.create_panel(channel)
            await interaction.followup.send(f"✅ Panneau configuré dans le canal {channel.mention}.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Temps écoulé. Veuillez réessayer la commande `/setup`.", ephemeral=True)


async def setup(bot):
    """Ajoute le cog ControlPanel au bot et recharge un panneau existant si nécessaire."""
    control_panel = ControlPanel(bot)
    await bot.add_cog(control_panel)
    await control_panel.load_panel()
