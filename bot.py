import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import datetime
import logging

# =========================
# CẤU HÌNH LOG (ẨN CONSOLE)
# =========================
# Tắt tất cả log không cần thiết từ discord.py
logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

# Chỉ hiển thị log lỗi nghiêm trọng của bot
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load token từ file .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("Thiếu DISCORD_TOKEN trong file .env hoặc biến môi trường")

# =========================
# CẤU HÌNH KÊNH LOG
# =========================
# THAY ID NÀY BẰNG ID KÊNH LOG KILL DINO CỦA BẠN
LOG_CHANNEL_ID = 123456789012345678  # <--- SỬA ID NÀY

# Biến toàn cục lưu ID tin nhắn log duy nhất
LOG_MESSAGE_ID = None

# =========================
# KHỞI TẠO BOT
# =========================
class KillLogBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Đồng bộ lệnh Slash toàn cầu
        await self.tree.sync()
        # Không in ra console để tránh log rác
        # print("Bot đã sẵn sàng và đồng bộ lệnh Slash!")

    async def on_ready(self):
        # Không in ra console
        # print(f"Bot online: {self.user}")
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
        placeholder="Ví dụ: 100%", 
        required=True
    )
    dino_id = discord.ui.TextInput(
        label="ID Dino đã chết", 
        placeholder="Nhập ID của Dino...", 
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
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")

        log_content = (
            f"**📌 KILL LOG MỚI NHẤT**\n"
            f"**Server:** {self.server_name}\n"
            f"**Dino:** {self.dino_name}\n"
            f"**Người chơi:** {name}\n"
            f"**Growth:** {growth_val}\n"
            f"**ID Dino:** {dino_id}\n"
            f"**Thời gian:** {timestamp}"
        )

        await interaction.response.send_message("✅ Đã ghi nhận Kill Log!", ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            logging.error(f"Không tìm thấy kênh Log với ID: {LOG_CHANNEL_ID}")
            return

        global LOG_MESSAGE_ID

        if LOG_MESSAGE_ID:
            try:
                old_message = await log_channel.fetch_message(LOG_MESSAGE_ID)
                await old_message.edit(content=log_content)
                return
            except discord.NotFound:
                pass

        new_message = await log_channel.send(log_content)
        LOG_MESSAGE_ID = new_message.id

# =========================
# VIEW (GIAO DIỆN CHỌN SERVER & DINO)
# =========================
class ServerSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="HỖ TRỢ / KILL LOG", style=discord.ButtonStyle.primary, custom_id="btn_kill_log")
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
        description="Nhấn nút bên dưới để bắt đầu ghi nhận Kill Log.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="League Ultra Dino")
    await interaction.response.send_message(embed=embed, view=ServerSelectView())

# =========================
# CHẠY BOT
# =========================
if __name__ == "__main__":
    # Ẩn log khởi động
    # print("Đang khởi động Kill Log Bot...")
    bot.run(TOKEN)
