import os
import asyncio
import discord

from discord import app_commands
from gtts import gTTS

TOKEN = (
    os.getenv("DISCORD_TOKEN")
    or os.getenv("DISCORD_BOT_TOKEN")
    or os.getenv("BOT_TOKEN")
    or os.getenv("TOKEN")
)

GUILD_ID = os.getenv("GUILD_ID")

if not TOKEN:
    raise RuntimeError("Thieu DISCORD_TOKEN trong FadeHost.")


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


def make_voice(text):
    filename = "google_voice.mp3"
    gTTS(text=text, lang="vi", slow=False).save(filename)
    return filename


@bot.tree.command(
    name="n",
    description="Bot doc van ban bang giong Google"
)
@app_commands.describe(text="Nhap noi dung muon bot doc")
@app_commands.guild_only()
async def speak(interaction: discord.Interaction, text: str):
    await interaction.response.defer(thinking=True)

    if not text.strip():
        await interaction.followup.send(
            "Ban chua nhap noi dung."
        )
        return

    if len(text) > 300:
        await interaction.followup.send(
            "Moi lan chi doc toi da 300 ky tu."
        )
        return

    member = interaction.guild.get_member(interaction.user.id)

    if member is None or member.voice is None:
        await interaction.followup.send(
            "Hay vao phong thoai truoc khi dung /n."
        )
        return

    channel = member.voice.channel
    voice_client = interaction.guild.voice_client
    filename = None

    try:
        if voice_client is None:
            voice_client = await channel.connect(
                timeout=20,
                self_deaf=True
            )
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        # Tu deafen bot, ke ca khi bot da ket noi san
        await interaction.guild.change_voice_state(
            channel=voice_client.channel,
            self_deaf=True,
            self_mute=False
        )

        if voice_client.is_playing():
            voice_client.stop()

        filename = await asyncio.to_thread(make_voice, text)

        source = discord.FFmpegPCMAudio(filename)

        def after_play(error):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except OSError:
                pass

            if error:
                print(f"Loi phat am thanh: {error}")

        voice_client.play(source, after=after_play)

        await interaction.followup.send(
            f"🔊 Dang doc: **{discord.utils.escape_markdown(text)}**"
        )

    except Exception as error:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass

        print(f"Loi /n: {type(error).__name__}: {error}")

        await interaction.followup.send(
            f"Khong doc duoc: `{type(error).__name__}: {error}`"
        )


@bot.tree.command(
    name="stop",
    description="Dung giong doc"
)
@app_commands.guild_only()
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client and (
        voice_client.is_playing() or voice_client.is_paused()
    ):
        voice_client.stop()
        await interaction.response.send_message(
            "Da dung giong doc."
        )
    else:
        await interaction.response.send_message(
            "Bot khong dang doc gi ca."
        )


@bot.tree.command(
    name="leave",
    description="Cho bot roi phong thoai"
)
@app_commands.guild_only()
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        await interaction.response.send_message(
            "Bot khong o trong phong thoai."
        )
        return

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await voice_client.disconnect(force=True)

    await interaction.response.send_message(
        "Bot da roi phong thoai."
    )


print("Dang khoi dong League Ultra Dino...")
bot.run(TOKEN)
