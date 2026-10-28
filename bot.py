
import os
import asyncio
import discord
import yt_dlp
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.voice_states = True


class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if not GUILD_ID:
            raise RuntimeError("Thiếu biến môi trường GUILD_ID trong FadeHost")

        guild = discord.Object(id=int(GUILD_ID))
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"Đã đồng bộ {len(synced)} lệnh vào máy chủ {GUILD_ID}:")
        for command in synced:
            print(f"- /{command.name}")


bot = LeagueUltraDino()


@bot.event
async def on_ready():
    print(f"League Ultra Dino online: {bot.user}")


@bot.tree.command(name="pl", description="Phát nhạc từ link YouTube")
@app_commands.describe(link="Đường link bài nhạc YouTube")
async def pl(interaction: discord.Interaction, link: str):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ dùng trong máy chủ Discord.",
            ephemeral=True
        )
        return

    voice_state = getattr(interaction.user, "voice", None)
    if voice_state is None or voice_state.channel is None:
        await interaction.response.send_message(
            "Bạn hãy vào phòng thoại trước nhé.",
            ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)

    try:
        channel = voice_state.channel
        vc = interaction.guild.voice_client

        if vc is None:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        def get_audio_info():
            options = {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(link, download=False)

        info = await asyncio.to_thread(get_audio_info)
        audio_url = info.get("url")
        title = info.get("title", "Không rõ tên bài")

        if not audio_url:
            raise RuntimeError("Không lấy được đường dẫn âm thanh từ YouTube.")

        if vc.is_playing() or vc.is_paused():
            vc.stop()

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options=(
                "-reconnect 1 -reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            options="-vn"
        )

        vc.play(source)
        await interaction.followup.send(f"🎵 Đang phát: **{title}**")

    except Exception as e:
        print(f"Lỗi phát nhạc: {type(e).__name__}: {e}")
        await interaction.followup.send(
            f"❌ Không phát được nhạc: `{type(e).__name__}: {e}`"
        )


@bot.tree.command(name="stop", description="Dừng phát nhạc")
async def stop(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ dùng trong máy chủ Discord.",
            ephemeral=True
        )
        return

    vc = interaction.guild.voice_client
    if vc is None or not (vc.is_playing() or vc.is_paused()):
        await interaction.response.send_message(
            "Hiện không có bài nhạc nào đang phát.",
            ephemeral=True
        )
        return

    vc.stop()
    await interaction.response.send_message("⏹️ Đã dừng nhạc.")


@bot.tree.command(name="leave", description="Cho bot rời phòng thoại")
async def leave(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "Lệnh này chỉ dùng trong máy chủ Discord.",
            ephemeral=True
        )
        return

    vc = interaction.guild.voice_client
    if vc is None:
        await interaction.response.send_message(
            "Bot hiện không ở trong phòng thoại.",
            ephemeral=True
        )
        return

    await vc.disconnect()
    await interaction.response.send_message(
        "👋 Bot đã rời phòng thoại."
    )


if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường DISCORD_TOKEN")

bot.run(TOKEN)
