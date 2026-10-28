
import os
import asyncio
import discord
import yt_dlp
from discord import app_commands

# =========================
# CẤU HÌNH
# =========================

TOKEN = (
    os.getenv("DISCORD_TOKEN")
    or os.getenv("DISCORD_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.voice_states = True


# =========================
# BOT
# =========================

class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("Đang khởi tạo lệnh Discord...")

        commands = self.tree.get_commands()
        print("Lệnh đã khai báo:", [cmd.name for cmd in commands])

        if not GUILD_ID:
            raise RuntimeError(
                "Thiếu GUILD_ID trong Environment Variables của FadeHost"
            )

        guild = discord.Object(id=int(GUILD_ID))

        # Đồng bộ lệnh vào máy chủ để hiện nhanh
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"Đã đồng bộ {len(synced)} lệnh vào máy chủ {GUILD_ID}")

        for command in synced:
            print(f"Đã đăng ký: /{command.name}")


bot = LeagueUltraDino()


# =========================
# KHI BOT ONLINE
# =========================

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    print(f"Bot ID: {bot.user.id}")


# =========================
# LỆNH /PL
# =========================

@bot.tree.command(
    name="pl",
    description="Phát nhạc từ đường link YouTube"
)
@app_commands.describe(
    link="Dán đường link bài nhạc YouTube"
)
async def pl(interaction: discord.Interaction, link: str):

    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ sử dụng trong máy chủ Discord.",
            ephemeral=True
        )
        return

    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message(
            "Bạn cần vào phòng thoại trước khi phát nhạc.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        # Tham gia hoặc chuyển phòng thoại
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        # Lấy thông tin âm thanh từ YouTube
        def extract_audio():
            options = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(link, download=False)

        info = await asyncio.to_thread(extract_audio)

        audio_url = info.get("url")
        title = info.get("title", "Không rõ tên bài")

        if not audio_url:
            raise RuntimeError("Không lấy được đường dẫn âm thanh.")

        # Dừng bài hiện tại nếu đang phát
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        # Phát nhạc bằng FFmpeg
        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options=(
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            options="-vn"
        )

        voice_client.play(source)

        await interaction.followup.send(
            f"🎵 Đang phát: **{title}**"
        )

    except Exception as error:
        print(
            f"Lỗi /pl: {type(error).__name__}: {error}"
        )

        await interaction.followup.send(
            f"❌ Không phát được nhạc: "
            f"`{type(error).__name__}: {error}`"
        )


# =========================
# LỆNH /STOP
# =========================

@bot.tree.command(
    name="stop",
    description="Dừng phát nhạc"
)
async def stop(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ sử dụng trong máy chủ.",
            ephemeral=True
        )
        return

    voice_client = interaction.guild.voice_client

    if voice_client and (
        voice_client.is_playing() or voice_client.is_paused()
    ):
        voice_client.stop()
        await interaction.response.send_message(
            "⏹️ Đã dừng nhạc."
        )
    else:
        await interaction.response.send_message(
            "Hiện không có nhạc đang phát.",
            ephemeral=True
        )


# =========================
# LỆNH /LEAVE
# =========================

@bot.tree.command(
    name="leave",
    description="Cho bot rời phòng thoại"
)
async def leave(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ sử dụng trong máy chủ.",
            ephemeral=True
        )
        return

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.response.send_message(
            "Bot hiện không ở trong phòng thoại.",
            ephemeral=True
        )
        return

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await voice_client.disconnect()

    await interaction.response.send_message(
        "👋 League Ultra Dino đã rời phòng thoại."
    )


# =========================
# CHẠY BOT
# =========================

if not TOKEN:
    raise RuntimeError(
        "Không tìm thấy token. Hãy đặt DISCORD_TOKEN "
        "trong Environment Variables."
    )

bot.run(TOKEN)
