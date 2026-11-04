import os
import discord
from discord.ext import commands
from discord import app_commands
import datetime
import logging

# =========================
# CẤU HÌNH LOG (ẨN CONSOLE)
# =========================
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Lấy token từ biến môi trường (FadeHost)
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("Thiếu DISCORD_TOKEN trong biến môi trường của FadeHost")

# =========================
# CẤU HÌNH KÊNH LOG
# =========================
# ID kênh Log của bạn
LOG_CHANNEL_ID = 1567394939317518507

# =========================
# KHỞI TẠO BOT
# =========================
class KillLogBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        pass

bot = KillLogBot()

# =========================
# MODAL (BẢNG NHẬP THÔNG TIN)
# =========================
class KillLogModal(discord.ui.Modal, title="Nhập thông tin Kill Log"):
    player_name = discord.ui.TextInput(
        label="Tên người chơi", 
        placeholder="Nhập tên người chơi...", 
        required=True
    )
    growth = discord.ui.TextInput(
        label="Growth (Độ lớn)", 
        placeholder="Ví dụ: 86", 
        required=True
    )
    dino_id = discord.ui.TextInput(
        label="ID Dino đã chết", 
        placeholder="Nhập ID của Dino...", 
        required=True
    )
    kill_time = discord.ui.TextInput(
        label="Thời gian giết", 
        placeholder="Ví dụ: 04:40:46 04/11/2026", 
        required=True
    )

    def __init__(self, server_name, dino_name):
        super().__init__()
        self.server_name = server_name
        self.dino_name = dino_name

    async def on_submit(self, interaction: discord.Interaction):
        name = self.player_name.value
        growth_val = self.growth.value
        dino_id = self.dino_id.value
        k_time = self.kill_time.value

        # Nội dung log (Đã đổi thành KILL LOG)
        log_content = (
            f"**📌 KILL LOG**\n"
            f"**Server:** {self.server_name}\n"
            f"**Dino:** {self.dino_name}\n"
            f"**Người chơi:** {name}\n"
            f"**Growth:** {growth_val}\n"
            f"**ID Dino:** {dino_id}\n"
            f"**Thời gian giết:** {k_time}"
        )

        await interaction.response.send_message("✅ Đã ghi nhận Kill Log!", ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            logging.error(f"Không tìm thấy kênh Log với ID: {LOG_CHANNEL_ID}")
            return

        # Gửi tin nhắn mới (Không xóa/sửa tin nhắn cũ)
        await log_channel.send(log_content)

# =========================
# VIEW (GIAO DIỆN CHỌN SERVER & DINO)
# =========================
class ServerSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="LOG KILL", style=discord.ButtonStyle.danger, custom_id="btn_kill_log")
    async def support_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Vui lòng chọn Server và Dino bên dưới:", ephemeral=True, view=DinoSelectView())

class DinoSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Chọn Server...",
        options=[
            discord.SelectOption(label="Server VIP", value="VIP"),
            discord.SelectOption(label="Server Premium", value="Premium"),
            discord.SelectOption(label="Server Ultra", value="Ultra"),
        ]
    )
    async def select_server(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_message(f"Bạn đã chọn Server: **{select.values[0]}**\nVui lòng chọn Dino:", ephemeral=True, view=DinoTypeSelectView(select.values[0]))

class DinoTypeSelectView(discord.ui.View):
    def __init__(self, server_name):
        super().__init__(timeout=None)
        self.server_name = server_name

    @discord.ui.select(
        placeholder="Chọn loài Dino...",
        options=[
            discord.SelectOption(label="Tyrannosaurus", value="Tyrannosaurus"),
            discord.SelectOption(label="Triceratops", value="Triceratops"),
            discord.SelectOption(label="Allosaurus", value="Allosaurus"),
            discord.SelectOption(label="Stegosaurus", value="Stegosaurus"),
            discord.SelectOption(label="Deinosuchus", value="Deinosuchus"),
            discord.SelectOption(label="Ceratosaurus", value="Ceratosaurus"),
            discord.SelectOption(label="Pachycephalosaurus", value="Pachycephalosaurus"),
            discord.SelectOption(label="Tenontosaurus", value="Tenontosaurus"),
            discord.SelectOption(label="Omniraptor", value="Omniraptor"),
            discord.SelectOption(label="Hypsilophodon", value="Hypsilophodon"),
            discord.SelectOption(label="Beipiaosaurus", value="Beipiaosaurus"),
            discord.SelectOption(label="Carnotaurus", value="Carnotaurus"),
            discord.SelectOption(label="Diabloceratops", value="Diabloceratops"),
            discord.SelectOption(label="Dilophosaurus", value="Dilophosaurus"),
            discord.SelectOption(label="Dryosaurus", value="Dryosaurus"),
            discord.SelectOption(label="Gallimimus", value="Gallimimus"),
            discord.SelectOption(label="Herrerasaurus", value="Herrerasaurus"),
            discord.SelectOption(label="Maiasaura", value="Maiasaura"),
            discord.SelectOption(label="Pteranodon", value="Pteranodon"),
            discord.SelectOption(label="Sauropelta", value="Sauropelta"),
            discord.SelectOption(label="Suchomimus", value="Suchomimus"),
            discord.SelectOption(label="Troodon", value="Troodon"),
            discord.SelectOption(label="Tyrannosaurus Rex", value="Tyrannosaurus Rex"),
        ]
    )
    async def select_dino(self, interaction: discord.Interaction, select: discord.ui.Select):
        dino_name = select.values[0]
        await interaction.response.send_modal(KillLogModal(self.server_name, dino_name))

# =========================
# LỆNH SLASH /SETUP_KILL_LOG
# =========================
@bot.tree.command(name="setup_kill_log", description="Tạo bảng chọn Server và Dino để ghi Kill Log")
async def setup_kill_log(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 HỆ THỐNG KILL LOG DINO",
        description="Nhấn nút **LOG KILL** bên dưới để bắt đầu ghi nhận.",
        color=discord.Color.red()
    )
    embed.set_footer(text="League Ultra Dino")
    await interaction.response.send_message(embed=embed, view=ServerSelectView())

# =========================
# CHẠY BOT
# =========================
if __name__ == "__main__":
    bot.run(TOKEN)
