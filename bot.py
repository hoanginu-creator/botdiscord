
import os
import asyncio
import discord
import yt_dlp
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True


class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = LeagueUltraDino()

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn",
}


@bot.event
async def on_ready():
    print(f"🦖 League Ultra Dino online: {bot.user}")


@bot.tree.command(name="ping", description="Kiem tra bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🦖 League Ultra Dino đang hoạt động!"
    )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.content.startswith("!l "):
        return

    url = message.content[3:].strip()

    if not url.startswith(("https://", "http://")):
        await message.channel.send(
            "❌ Hãy nhập link hợp lệ: `!l LINK`"
        )
        return

    if not message.guild:
        return

    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send(
            "❌ Bạn cần vào kênh thoại trước!"
        )
        return

    voice_channel = message.author.voice.channel
    voice_client = message.guild.voice_client

    try:
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        if voice_client.is_playing():
            voice_client.stop()

        await message.channel.send("🔎 Đang tải thông tin âm thanh...")

        def get_audio_info():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                return ydl.extract_info(url, download=False)

        info = await asyncio.to_thread(get_audio_info)
        audio_url = info["url"]
        title = info.get("title", "Không rõ tên bài")

        source = discord.FFmpegPCMAudio(
            audio_url,
            **FFMPEG_OPTIONS
        )

        voice_client.play(source)

        await message.channel.send(
            f"🎵 Đang phát: **{title}**"
        )

    except Exception as e:
        print(f"Lỗi phát nhạc: {e}")
        await message.channel.send(
            "❌ Không phát được nhạc. Kiểm tra FFmpeg, "
            "quyền kênh thoại và link âm thanh."
        )


if not TOKEN:
    raise RuntimeError("Chua co DISCORD_TOKEN")

bot.run(TOKEN)
