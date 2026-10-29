
import os
import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = LeagueUltraDino()

@bot.event
async def on_ready():
    print(f"🦖 League Ultra Dino online: {bot.user}")

@bot.tree.command(name="ping", description="Kiem tra bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🦖 League Ultra Dino đang hoạt động!"
    )

if not TOKEN:
    raise RuntimeError("Chua co DISCORD_TOKEN")

bot.run(TOKEN)
