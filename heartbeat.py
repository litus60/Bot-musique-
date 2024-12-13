import time
import threading
import asyncio

def heartbeat(bot, channel_id):
    """Envoie un ping toutes les X minutes pour montrer que le bot fonctionne."""
    async def send_heartbeat():
        while True:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send("✅ **Heartbeat :** Le bot est toujours en ligne.")
            await asyncio.sleep(300)  # 5 minutes

    # Exécute la tâche de manière asynchrone
    asyncio.run_coroutine_threadsafe(send_heartbeat(), bot.loop)
