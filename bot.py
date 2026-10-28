
import os
import asyncio
import discord
import yt_dlp
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True

class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("Đã đồng bộ lệnh slash.")

bot = LeagueUltraDino()

@bot.event
async def on_ready():
    print(f"League Ultra Dino online: {bot.user}")

@bot.tree.command(name="pl", description="Phát nhạc từ link YouTube")
@app_commands.describe(link="Đường link bài nhạc YouTube")
async def pl(interaction: discord.Interaction, link: str):
    if not interaction.guild:
        await interaction.response.send_message(
            "Lệnh này chỉ dùng trong máy chủ.", ephemeral=True
        )
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message(
            "Bạn cần vào phòng thoại trước.", ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        if vc is None:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        def get_info():
            options = {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(link, download=False)

        info = await asyncio.to_thread(get_info)
        audio_url = info["url"]
        title = info.get("title", "Không rõ tên bài")

        if vc.is_playing():
            vc.stop()

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )
        vc.play(source)

        await interaction.followup.send(f"🎵 Đang phát: **{title}**")

    except Exception as e:
        print(f"Lỗi phát nhạc: {type(e).__name__}: {e}")
        await interaction.followup.send(
            f"Không phát được nhạc: `{type(e).__name__}: {e}`"
        )

if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường DISCORD_TOKEN")

bot.run(TOKEN)
