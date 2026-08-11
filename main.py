# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import re
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

intents = discord.Intents.default()
intents.message_content = True

class NotificationBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("✅ ซิงค์ Slash Commands (/setup) เรียบร้อยแล้ว")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการซิงค์: {e}")

bot = NotificationBot()

# ------------------------------------------
# ฟังก์ชันช่วยค้นหา Emoji (รวมถึง Custom Emoji จากเซิร์ฟอื่น)
# ------------------------------------------
def resolve_emoji(emoji_input: str):
    if not emoji_input:
        return "📢"
    
    clean_input = emoji_input.strip()
    
    # กรณีผู้ใช้พิมพ์รูปแบบ :emoji_name:
    match = re.match(r"^:([a-zA-Z0-9_]+):$", clean_input)
    if match:
        emoji_name = match.group(1)
        found_emoji = discord.utils.get(bot.emojis, name=emoji_name)
        if found_emoji:
            return str(found_emoji)
            
    return clean_input

# ------------------------------------------
# 1. หน้าต่าง Modal กรอกข้อมูลทุกอย่างจบในหน้าเดียว
# ------------------------------------------
class SingleSetupModal(discord.ui.Modal, title="ตั้งค่าและส่งข้อความแจ้งเตือน"):
    channel_input = discord.ui.TextInput(
        label="ชื่อช่องข้อความที่จะส่ง (เช่น general หรือข่าวสาร)",
        style=discord.TextStyle.short,
        placeholder="พิมพ์ชื่อช่อง เช่น general (ไม่ต้องใส่ #)",
        required=True,
    )

    title_input = discord.ui.TextInput(
        label="หัวข้อประกาศ",
        style=discord.TextStyle.short,
        placeholder="เช่น โปรโมชั่นพิเศษประจำเดือน",
        required=True,
        max_length=100,
    )

    message_input = discord.ui.TextInput(
        label="เนื้อหาข้อความแจ้งเตือน",
        style=discord.TextStyle.paragraph,
        placeholder="รายละเอียดข้อความที่จะประกาศ...",
        required=True,
        max_length=2000,
    )

    emoji_input = discord.ui.TextInput(
        label="Emoji นำหน้าหัวข้อ (พิมพ์ชื่อเช่น :cart: ได้)",
        style=discord.TextStyle.short,
        placeholder="เช่น :cart: หรือ 📢 (หากเว้นว่างใช้ 📢)",
        required=False,
    )

    extra_input = discord.ui.TextInput(
        label="รูปแบนเนอร์ | ชื่อปุ่มเว็บ | URL เว็บไซต์",
        style=discord.TextStyle.short,
        placeholder="คั่นด้วย | เช่น https://image.png | สั่งซื้อ | https://site.com",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # 1. ค้นหาช่องข้อความจากชื่อที่พิมพ์
        target_channel_name = self.channel_input.value.strip().lstrip("#")
        target_channel = discord.utils.get(interaction.guild.text_channels, name=target_channel_name)

        if not target_channel:
            await interaction.followup.send(f"❌ ไม่พบช่องข้อความชื่อ **#{target_channel_name}** ในเซิร์ฟเวอร์นี้", ephemeral=True)
            return

        # 2. แปลงค่า Emoji (รองรับ Custom Emoji ข้ามเซิร์ฟ)
        selected_emoji = resolve_emoji(self.emoji_input.value)

        # 3. แยกค่ารูปภาพ และ ปุ่มเว็บไซต์จากช่อง extra_input
        banner_url = None
        btn_label = None
        btn_url = None

        if self.extra_input.value:
            parts = [p.strip() for p in self.extra_input.value.split("|")]
            if len(parts) >= 1 and parts[0]:
                banner_url = parts[0]
            if len(parts) >= 2 and parts[1]:
                btn_label = parts[1]
            if len(parts) >= 3 and parts[2]:
                btn_url = parts[2]

        # 4. สร้าง Embed ประกาศ
        embed = discord.Embed(
            title=f"{selected_emoji} {self.title_input.value}",
            description=self.message_input.value,
            color=discord.Color.from_rgb(88, 101, 242),
            timestamp=datetime.now(),
        )

        embed.set_footer(
            text=f"ประกาศโดย {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
        )

        if banner_url and (banner_url.startswith("http://") or banner_url.startswith("https://")):
            embed.set_image(url=banner_url)

        # 5. สร้างปุ่มกดลิงก์เว็บไซต์ (ถ้ามี)
        out_view = None
        if btn_url and btn_label:
            if not (btn_url.startswith("http://") or btn_url.startswith("https://")):
                btn_url = "https://" + btn_url

            out_view = discord.ui.View(timeout=None)
            out_view.add_item(
                discord.ui.Button(
                    label=btn_label,
                    url=btn_url,
                    style=discord.ButtonStyle.link,
                    emoji="🌐",
                )
            )

        # 6. ส่งข้อความพร้อมแท็ก @everyone
        try:
            content_text = "@everyone"
            if out_view:
                await target_channel.send(content=content_text, embed=embed, view=out_view)
            else:
                await target_channel.send(content=content_text, embed=embed)

            await interaction.followup.send(f"✅ ส่งประกาศพร้อมแท็ก @everyone ไปยังช่อง {target_channel.mention} เรียบร้อยแล้ว!", ephemeral=True)
        except Exception as err:
            await interaction.followup.send(f"❌ ไม่สามารถส่งข้อความได้ โปรดตรวจสอบสิทธิ์ของบอท: {err}", ephemeral=True)


# ------------------------------------------
# 2. แผงควบคุมที่มีปุ่มเดียว
# ------------------------------------------
class SetupControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 คลิกที่นี่เพื่อกรอกข้อมูลและส่งประกาศ", style=discord.ButtonStyle.success, custom_id="btn_single_setup")
    async def btn_single_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SingleSetupModal())


# ------------------------------------------
# 3. คำสั่ง /setup
# ------------------------------------------
@bot.tree.command(name="setup", description="เปิดหน้าต่างสร้างประกาศแจ้งเตือนพร้อมแท็กทุกคน")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ ระบบสร้างประกาศแจ้งเตือนอัตโนมัติ",
        description=(
            "กดปุ่มสีเขียวด้านล่างเพียงปุ่มเดียว เพื่อกรอกข้อมูลทั้งหมดและส่งประกาศทันที!\n\n"
            "📌 **ฟังก์ชันเด่น:**\n"
            "• แท็ก **@everyone** ให้อัตโนมัติทุกประกาศ\n"
            "• รองรับ Custom Emoji ข้ามเซิร์ฟเวอร์ (ใส่แบบ `:cart:`, `:fire:`)\n"
            "• สามารถแนบรูปแบนเนอร์และสร้างปุ่มลิงก์ Website ได้พร้อมกัน"
        ),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, view=SetupControlView(), ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์พร้อมใช้งาน: {bot.user.name}")

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN.strip())
else:
    print("❌ ไม่พบ DISCORD_TOKEN")
