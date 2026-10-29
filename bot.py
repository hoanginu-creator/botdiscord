import os
import asyncio

import discord
import yt_dlp

from discord import app_commands

TOKEN = (
    os.getenv("DISCORD_TOKEN")
    or os.getenv("DISCORD_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN:
    raise RuntimeError("Thieu DISCORD_TOKEN trong FadeHost.")


# =========================
# YT-DLP CONFIG
# =========================
YTDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


# =========================
# MUSIC PLAYER (per guild)
# =========================
class MusicPlayer:
    def __init__(self):
        self.queue = []          # list[{url, title}]
        self.current = None      # dict {url, title}
        self.voice_client = None
        self.text_channel = None # de gui thong bao khi auto-next

    def add(self, url, title):
        self.queue.append({"url": url, "title": title})

    def next(self):
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        self.current = None
        return None

    def clear(self):
        self.queue.clear()
        self.current = None


music_players: dict[int, MusicPlayer] = {}


def get_player(guild_id: int) -> MusicPlayer:
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer()
    return music_players[guild_id]


# =========================
# YOUTUBE HELPERS
# =========================
def search_youtube(query: str):
    """Tim kiem YouTube, tra ve (url, title)."""
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if info and info.get("entries"):
            entry = info["entries"][0]
            return entry["webpage_url"], entry["title"]
    return None, None


def get_stream_url(url: str):
    """Lay stream URL truc tiep tu YouTube."""
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"], info.get("title", "Unknown")


# =========================
# BOT CLIENT
# =========================
class LeagueUltraDino(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        print(f"Da dong bo {len(synced)} lenh.")

    async def on_ready(self):
        print(f"Bot online: {self.user}")


bot = LeagueUltraDino()


# =========================
# CORE PLAY LOGIC
# =========================
async def play_next(guild: discord.Guild, player: MusicPlayer):
    """Phat bai tiep theo trong queue."""
    vc = player.voice_client
    if vc is None or not vc.is_connected():
        return

    song = player.next()
    if song is None:
        return

    try:
        stream_url, title = await asyncio.to_thread(get_stream_url, song["url"])
        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTS)

        def after_play(error):
            if error:
                print(f"Loi phat nhac: {error}")
            # Tiep tuc bai ke tiep
            fut = asyncio.run_coroutine_threadsafe(
                play_next(guild, player), bot.loop
            )
            try:
                fut.result(timeout=5)
            except Exception:
                pass

        vc.play(source, after=after_play)

        if player.text_channel:
            try:
                await player.text_channel.send(
                    f"🎵 Dang phat: **{discord.utils.escape_markdown(title)}**"
                )
            except Exception:
                pass

    except Exception as error:
        print(f"Loi play_next: {type(error).__name__}: {error}")
        if player.text_channel:
            try:
                await player.text_channel.send(
                    f"⚠️ Loi phat bai: `{type(error).__name__}: {error}`"
                )
            except Exception:
                pass
        # Thu bai tiep theo
        await play_next(guild, player)


async def ensure_voice(interaction: discord.Interaction):
    """Dam bao bot ket noi voice cung kenh voi user. Tra ve (vc, player) hoac (None, None)."""
    member = interaction.guild.get_member(interaction.user.id)
    if member is None or member.voice is None or member.voice.channel is None:
        await interaction.followup.send("Hay vao phong thoai truoc.")
        return None, None

    channel = member.voice.channel
    vc = interaction.guild.voice_client

    try:
        if vc is None:
            vc = await channel.connect(timeout=20, self_deaf=True)
        elif vc.channel != channel:
            await vc.move_to(channel)
    except Exception as error:
        await interaction.followup.send(
            f"Khong vao duoc phong thoai: `{type(error).__name__}: {error}`"
        )
        return None, None

    player = get_player(interaction.guild.id)
    player.voice_client = vc
    player.text_channel = interaction.channel
    return vc, player


# =========================
# SLASH COMMANDS
# =========================
@bot.tree.command(name="play", description="Phat nhac tu YouTube")
@app_commands.describe(query="Ten bai hat hoac link YouTube")
@app_commands.guild_only()
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    vc, player = await ensure_voice(interaction)
    if vc is None:
        return

    try:
        url, title = await asyncio.to_thread(search_youtube, query)
    except Exception as error:
        await interaction.followup.send(
            f"Khong tim thay bai hat: `{type(error).__name__}: {error}`"
        )
        return

    if not url:
        await interaction.followup.send("Khong tim thay bai hat.")
        return

    player.add(url, title)

    if vc.is_playing() or vc.is_paused():
        await interaction.followup.send(
            f"➕ Da them vao hang doi: **{discord.utils.escape_markdown(title)}**"
        )
    else:
        await interaction.followup.send(
            f"⏳ Dang chuan bi phat: **{discord.utils.escape_markdown(title)}**"
        )
        await play_next(interaction.guild, player)


@bot.tree.command(name="skip", description="Bo qua bai hien tai")
@app_commands.guild_only()
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()  # after_play se tu goi bai tiep
        await interaction.response.send_message("⏭️ Da bo qua bai hien tai.")
    else:
        await interaction.response.send_message("Bot khong dang phat nhac.")


@bot.tree.command(name="pause", description="Tam dung nhac")
@app_commands.guild_only()
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Da tam dung.")
    else:
        await interaction.response.send_message("Bot khong dang phat nhac.")


@bot.tree.command(name="resume", description="Tiep tuc phat nhac")
@app_commands.guild_only()
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Da tiep tuc.")
    else:
        await interaction.response.send_message("Bot khong dang tam dung.")


@bot.tree.command(name="queue", description="Xem hang doi nhac")
@app_commands.guild_only()
async def queue_cmd(interaction: discord.Interaction):
    player = get_player(interaction.guild.id)
    lines = []

    if player.current:
        lines.append(
            f"🎵 **Dang phat:** {discord.utils.escape_markdown(player.current['title'])}"
        )
    if player.queue:
        lines.append("")
        lines.append("📋 **Hang doi:**")
        for i, song in enumerate(player.queue[:10], start=1):
            lines.append(f"{i}. {discord.utils.escape_markdown(song['title'])}")
        if len(player.queue) > 10:
            lines.append(f"... va {len(player.queue) - 10} bai khac.")

    if not lines:
        await interaction.response.send_message("Hang doi dang trong.")
    else:
        await interaction.response.send_message("\n".join(lines))


@bot.tree.command(name="stop", description="Dung nhac va xoa hang doi")
@app_commands.guild_only()
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    player = get_player(interaction.guild.id)

    if vc and (vc.is_playing() or vc.is_paused()):
        player.clear()
        vc.stop()
        await interaction.response.send_message("⏹️ Da dung nhac va xoa hang doi.")
    else:
        await interaction.response.send_message("Bot khong dang phat nhac.")


@bot.tree.command(name="leave", description="Cho bot roi phong thoai")
@app_commands.guild_only()
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc is None:
        await interaction.response.send_message("Bot khong o trong phong thoai.")
        return

    player = get_player(interaction.guild.id)
    player.clear()

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    await vc.disconnect(force=True)
    await interaction.response.send_message("👋 Bot da roi phong thoai.")


print("Dang khoi dong League Ultra Dino...")
bot.run(TOKEN)
