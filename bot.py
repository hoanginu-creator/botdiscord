
import os
import asyncio
import discord
import yt_dlp
from discord import app_commands

# ==========================================
# CONFIGURATION
# ==========================================

TOKEN = (
    os.getenv("DISCORD_TOKEN")
    or os.getenv("DISCORD_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.voice_states = True


# ==========================================
# BOT CLIENT
# ==========================================

class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("Dang khoi tao League Ultra Dino...")

        if not GUILD_ID:
            raise RuntimeError(
                "Thieu GUILD_ID trong Environment Variables."
            )

        guild = discord.Object(id=int(GUILD_ID))

        # Khai bao cac slash command truoc khi dong bo
        self.tree.copy_global_to(guild=guild)

        commands = self.tree.get_commands()
        print(
            "Cac lenh da khai bao:",
            [command.name for command in commands]
        )

        synced = await self.tree.sync(guild=guild)

        print(
            f"Da dong bo {len(synced)} lenh vao server {GUILD_ID}"
        )

        for command in synced:
            print(f"Da dang ky: /{command.name}")

    async def on_error(self, event_method, *args, **kwargs):
        print(f"Loi su kien Discord: {event_method}")


bot = LeagueUltraDino()


# ==========================================
# BOT READY
# ==========================================

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    print(f"Bot ID: {bot.user.id}")


# ==========================================
# /PL - PLAY YOUTUBE
# ==========================================

@bot.tree.command(
    name="pl",
    description="Phat nhac tu link YouTube"
)
@app_commands.describe(
    link="Dan duong link bai nhac YouTube"
)
async def pl(
    interaction: discord.Interaction,
    link: str
):
    # Phai defer truoc khi xu ly tac vu lau
    await interaction.response.defer(thinking=True)

    if interaction.guild is None:
        await interaction.followup.send(
            "Lenh nay chi dung trong may chu Discord.",
            ephemeral=True
        )
        return

    if not interaction.user.voice:
        await interaction.followup.send(
            "Ban can vao phong thoai truoc.",
            ephemeral=True
        )
        return

    channel = interaction.user.voice.channel

    try:
        # Ket noi hoac chuyen phong thoai
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await asyncio.wait_for(
                channel.connect(timeout=15, reconnect=True),
                timeout=20
            )
        elif voice_client.channel != channel:
            await asyncio.wait_for(
                voice_client.move_to(channel),
                timeout=15
            )

        # Lay thong tin YouTube trong thread rieng
        def extract_audio():
            options = {
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "socket_timeout": 12,
                "retries": 1,
                "extractor_retries": 1,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(link, download=False)

        info = await asyncio.wait_for(
            asyncio.to_thread(extract_audio),
            timeout=30
        )

        audio_url = info.get("url")
        title = info.get("title", "Khong ro ten bai")

        if not audio_url:
            raise RuntimeError(
                "Khong lay duoc duong dan am thanh."
            )

        # Tao nguon am thanh
        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options=(
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            options="-vn"
        )

        # Dung bai cu neu dang phat
        if (
            voice_client.is_playing()
            or voice_client.is_paused()
        ):
            voice_client.stop()

        voice_client.play(source)

        await interaction.followup.send(
            f"🎵 Dang phat: **{title}**"
        )

    except asyncio.TimeoutError:
        print("Loi /pl: het thoi gian cho.")

        await interaction.followup.send(
            "⏱️ Tai nhac hoac ket noi qua lau. "
            "Hay thu lai sau."
        )

    except Exception as error:
        print(
            f"Loi /pl: {type(error).__name__}: {error}"
        )

        await interaction.followup.send(
            f"❌ Loi phat nhac: "
            f"`{type(error).__name__}: {error}`"
        )


# ==========================================
# /STOP - STOP MUSIC
# ==========================================

@bot.tree.command(
    name="stop",
    description="Dung phat nhac"
)
async def stop(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if interaction.guild is None:
        await interaction.followup.send(
            "Lenh nay chi dung trong may chu Discord.",
            ephemeral=True
        )
        return

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.followup.send(
            "Bot khong o trong phong thoai.",
            ephemeral=True
        )
        return

    if (
        voice_client.is_playing()
        or voice_client.is_paused()
    ):
        voice_client.stop()

        await interaction.followup.send(
            "⏹️ Da dung nhac."
        )
    else:
        await interaction.followup.send(
            "Hien khong co nhac dang phat.",
            ephemeral=True
        )


# ==========================================
# /LEAVE - LEAVE VOICE CHANNEL
# ==========================================

@bot.tree.command(
    name="leave",
    description="Cho bot roi phong thoai"
)
async def leave(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    if interaction.guild is None:
        await interaction.followup.send(
            "Lenh nay chi dung trong may chu Discord.",
            ephemeral=True
        )
        return

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.followup.send(
            "Bot khong o trong phong thoai.",
            ephemeral=True
        )
        return

    try:
        if (
            voice_client.is_playing()
            or voice_client.is_paused()
        ):
            voice_client.stop()

        await asyncio.wait_for(
            voice_client.disconnect(force=True),
            timeout=10
        )

        await interaction.followup.send(
            "👋 League Ultra Dino da roi phong thoai."
        )

    except Exception as error:
        print(
            f"Loi /leave: {type(error).__name__}: {error}"
        )

        await interaction.followup.send(
            f"Khong the roi phong: "
            f"`{type(error).__name__}: {error}`"
        )


# ==========================================
# START BOT
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "Khong tim thay token. "
        "Hay dat DISCORD_TOKEN trong FadeHost."
    )

bot.run(TOKEN)
