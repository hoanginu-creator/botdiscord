
import os
import asyncio
import discord
import yt_dlp

from discord import app_commands

# ==========================================
# CONFIG
# ==========================================

TOKEN = (
    os.getenv("DISCORD_TOKEN")
    or os.getenv("DISCORD_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN:
    raise RuntimeError(
        "Thieu token bot. Hay them DISCORD_TOKEN trong FadeHost."
    )

# ==========================================
# YOUTUBE CONFIG
# ==========================================

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "extract_flat": False,
    "socket_timeout": 20,
    "retries": 2,
    "extractor_retries": 2,
    "extractor_args": {
        "youtube": {
            "player_client": ["android_vr"]
        }
    },
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn",
}

# ==========================================
# DISCORD CLIENT
# ==========================================

class LeagueUltraDino(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("Dang dong bo slash commands...")

        if GUILD_ID:
            try:
                guild = discord.Object(id=int(GUILD_ID))
            except ValueError:
                raise RuntimeError("GUILD_ID khong hop le.")

            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(
                f"Da dong bo {len(synced)} lenh "
                f"vao server {GUILD_ID}."
            )
        else:
            synced = await self.tree.sync()
            print(
                f"Da dong bo {len(synced)} lenh toan cuc. "
                "Lenh co the mat mot luc moi hien."
            )

    async def on_ready(self):
        print(f"Bot online: {self.user} (ID: {self.user.id})")
        print("League Ultra Dino san sang!")


bot = LeagueUltraDino()

# ==========================================
# HELPERS
# ==========================================

def get_user_voice_channel(interaction: discord.Interaction):
    if interaction.guild is None:
        return None

    member = interaction.guild.get_member(interaction.user.id)

    if member is None or member.voice is None:
        return None

    return member.voice.channel


async def join_user_channel(interaction: discord.Interaction):
    channel = get_user_voice_channel(interaction)

    if channel is None:
        raise ValueError(
            "Ban can vao phong thoai truoc khi dung lenh nay."
        )

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await channel.connect(
            timeout=20,
            reconnect=True
        )
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    return voice_client, channel


def extract_youtube_info(query: str):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        info = ydl.extract_info(query, download=False)

        if info and "entries" in info:
            info = next(
                (entry for entry in info["entries"] if entry),
                None
            )

        if not info:
            raise ValueError("Khong tim thay bai hat.")

        return {
            "title": info.get("title", "Khong ro ten"),
            "webpage_url": info.get("webpage_url", query),
            "audio_url": info.get("url"),
        }


# ==========================================
# /JOIN
# ==========================================

@bot.tree.command(
    name="join",
    description="Goi bot vao phong thoai ban dang o"
)
@app_commands.guild_only()
async def join(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        _, channel = await join_user_channel(interaction)
        await interaction.followup.send(
            f"Da vao phong thoai **{channel.name}**!"
        )

    except Exception as error:
        print(f"Loi /join: {type(error).__name__}: {error}")
        await interaction.followup.send(
            f"Khong vao duoc phong: {error}"
        )


# ==========================================
# /PL
# ==========================================

@bot.tree.command(
    name="pl",
    description="Phat nhac YouTube"
)
@app_commands.describe(
    link="Link YouTube hoac ten bai hat"
)
@app_commands.guild_only()
async def pl(
    interaction: discord.Interaction,
    link: str
):
    await interaction.response.defer(thinking=True)

    try:
        voice_client, channel = await join_user_channel(interaction)

        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        await interaction.followup.send(
            "Dang tim bai hat..."
        )

        info = await asyncio.wait_for(
            asyncio.to_thread(extract_youtube_info, link),
            timeout=60
        )

        audio_url = info.get("audio_url")
        title = info.get("title", "Khong ro ten")
        webpage_url = info.get("webpage_url", link)

        if not audio_url:
            await interaction.followup.send(
                "Khong lay duoc link audio. Hay thu link khac."
            )
            return

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options=FFMPEG_OPTIONS["before_options"],
            options=FFMPEG_OPTIONS["options"],
        )

        voice_client.play(source)

        embed = discord.Embed(
            title="League Ultra Dino",
            description=f"**Dang phat:** [{title}]({webpage_url})",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Phong thoai",
            value=channel.name,
            inline=True
        )

        embed.set_footer(
            text=f"Yeu cau boi {interaction.user.display_name}"
        )

        await interaction.followup.send(embed=embed)

    except asyncio.TimeoutError:
        await interaction.followup.send(
            "Tim bai hat qua lau. Hay thu lai."
        )

    except ValueError as error:
        await interaction.followup.send(str(error))

    except Exception as error:
        print(f"Loi /pl: {type(error).__name__}: {error}")

        await interaction.followup.send(
            f"Khong phat duoc nhac: "
            f"`{type(error).__name__}: {error}`"
        )


# ==========================================
# /STOP
# ==========================================

@bot.tree.command(
    name="stop",
    description="Dung bai nhac dang phat"
)
@app_commands.guild_only()
async def stop(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.followup.send(
            "Bot chua o trong phong thoai."
        )
        return

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()
        await interaction.followup.send("Da dung nhac.")
    else:
        await interaction.followup.send(
            "Khong co bai nhac nao dang phat."
        )


# ==========================================
# /LEAVE
# ==========================================

@bot.tree.command(
    name="leave",
    description="Cho bot roi khoi phong thoai"
)
@app_commands.guild_only()
async def leave(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.followup.send(
            "Bot khong o trong phong thoai."
        )
        return

    try:
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

        await voice_client.disconnect(force=True)

        await interaction.followup.send(
            "Bot da roi phong thoai."
        )

    except Exception as error:
        print(f"Loi /leave: {type(error).__name__}: {error}")
        await interaction.followup.send(
            f"Khong roi duoc phong: {error}"
        )


# ==========================================
# START BOT
# ==========================================

print("Dang khoi tao League Ultra Dino...")
print("Lenh: join, pl, stop, leave")

bot.run(TOKEN)
