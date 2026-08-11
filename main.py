# -*- coding: utf-8 -*-
import os
import sys
import asyncio
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
        self.selected_channel_id = None
        self.selected_emoji = "📢"

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("✅ ซิงค์ Slash Commands (/setup) เรียบร้อยแล้ว")
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในการซิงค์: {e}")

bot = NotificationBot()

# ------------------------------------------
# 1. หน้าต่างกรอกข้อความ (Modal)
# ------------------------------------------
class MessageModal(discord.ui.Modal, title="กรอกรายละเอียดข้อความแจ้งเตือน"):
    title_input = discord.ui.TextInput(
        label="หัวข้อประกาศ",
        style=discord.TextStyle.short,
        placeholder="เช่น โปรโมชั่นพิเศษ / ปิดปรับปรุงระบบ",
        required=True,
        max_length=100,
    )

    message_input = discord.ui.TextInput(
        label="รายละเอียดข้อความ",
        style=discord.TextStyle.paragraph,
        placeholder="พิมพ์เนื้อหาข้อความแจ้งเตือนที่นี่...",
        required=True,
        max_length=2000,
    )

    image_url_input = discord.ui.TextInput(
        label="ลิงก์รูปแบนเนอร์ (ถ้าไม่มีให้เว้นว่าง)",
        style=discord.TextStyle.short,
        placeholder="https://...png หรือ jpg",
        required=False,
    )

    button_label_input = discord.ui.TextInput(
        label="ชื่อปุ่มเว็บไซต์ (ถ้าไม่มีให้เว้นว่าง)",
        style=discord.TextStyle.short,
        placeholder="เช่น เข้าสู่เว็บไซต์ / สั่งซื้อสินค้า",
        required=False,
        max_length=80,
    )

    button_url_input = discord.ui.TextInput(
        label="URL เว็บไซต์ (ถ้าไม่มีให้เว้นว่าง)",
        style=discord.TextStyle.short,
        placeholder="https://your-website.com",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # ตอบรับ Interaction ทันทีเพื่อป้องกัน Timeout
        await interaction.response.defer(ephemeral=True)

        if not bot.selected_channel_id:
            await interaction.followup.send("❌ กรุณาเลือกช่องที่จะส่งข้อความก่อนครับ!", ephemeral=True)
            return

        channel = bot.get_channel(bot.selected_channel_id)
        if channel:
            embed = discord.Embed(
                title=f"{bot.selected_emoji} {self.title_input.value}",
                description=self.message_input.value,
                color=discord.Color.from_rgb(88, 101, 242),
                timestamp=datetime.now(),
            )

            embed.set_footer(
                text=f"ประกาศโดย {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None,
            )

            if self.image_url_input.value and self.image_url_input.value.strip():
                embed.set_image(url=self.image_url_input.value.strip())

            # ปุ่มลิงก์เว็บไซต์แนบไปกับข้อความประกาศ
            out_view = None
            if self.button_url_input.value and self.button_label_input.value:
                url = self.button_url_input.value.strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url

                out_view = discord.ui.View(timeout=None)
                out_view.add_item(
                    discord.ui.Button(
                        label=self.button_label_input.value,
                        url=url,
                        style=discord.ButtonStyle.link,
                        emoji="🌐",
                    )
                )

            try:
                if out_view:
                    await channel.send(embed=embed, view=out_view)
                else:
                    await channel.send(embed=embed)

                await interaction.followup.send(f"✅ ส่งประกาศไปยังช่อง {channel.mention} เรียบร้อยแล้ว!", ephemeral=True)
            except Exception as err:
                await interaction.followup.send(f"❌ ส่งข้อความไม่สำเร็จ โปรดตรวจสอบสิทธิ์ของบอท: {err}", ephemeral=True)
        else:
            await interaction.followup.send("❌ ไม่พบช่องที่เลือก กรุณาตั้งค่าใหม่อีกครั้ง", ephemeral=True)


# ------------------------------------------
# 2. เมนูเลือกช่องแบบย่อย (Channel View)
# ------------------------------------------
class ChannelSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="คลิกเลือกช่องข้อความ..."
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        bot.selected_channel_id = select.values[0].id
        selected_chan = select.values[0]
        await interaction.response.send_message(f"✅ เลือกช่อง **#{selected_chan.name}** เรียบร้อยแล้ว!", ephemeral=True)


# ------------------------------------------
# 3. แผงปุ่มควบคุมหลัก (Main Setup Panel)
# ------------------------------------------
class SetupControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ปุ่มที่ 1: เลือกช่อง
    @discord.ui.button(label="📌 1. เลือกช่องที่จะส่ง", style=discord.ButtonStyle.primary, row=0, custom_id="btn_select_channel")
    async def btn_select_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("กรุณาเลือกช่องที่จะให้บอทส่งประกาศในเมนูด้านล่างนี้:", view=ChannelSelectView(), ephemeral=True)

    # ปุ่มกลุ่มที่ 2: เลือก Emoji
    @discord.ui.button(label="📢 ประกาศ", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_e1")
    async def emoji_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.selected_emoji = "📢"
        await interaction.response.send_message("✅ เลือก Emoji: 📢", ephemeral=True)

    @discord.ui.button(label="🛒 สินค้า", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_e2")
    async def emoji_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.selected_emoji = "🛒"
        await interaction.response.send_message("✅ เลือก Emoji: 🛒", ephemeral=True)

    @discord.ui.button(label="🎉 กิจกรรม", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_e3")
    async def emoji_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.selected_emoji = "🎉"
        await interaction.response.send_message("✅ เลือก Emoji: 🎉", ephemeral=True)

    @discord.ui.button(label="⚠️ เตือน", style=discord.ButtonStyle.secondary, row=1, custom_id="btn_e4")
    async def emoji_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot.selected_emoji = "⚠️"
        await interaction.response.send_message("✅ เลือก Emoji: ⚠️", ephemeral=True)

    # ปุ่มที่ 3: เปิดแบบฟอร์มกรอกข้อมูลเพื่อส่ง
    @discord.ui.button(label="📝 2. กรอกข้อมูล & รูป & ลิงก์ เพื่อส่งประกาศ", style=discord.ButtonStyle.success, row=2, custom_id="btn_open_modal")
    async def btn_open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not bot.selected_channel_id:
            await interaction.response.send_message("⚠️ กรุณากดปุ่ม **'📌 1. เลือกช่องที่จะส่ง'** ก่อนครับ!", ephemeral=True)
            return

        await interaction.response.send_modal(MessageModal())


# ------------------------------------------
# 4. คำสั่ง /setup
# ------------------------------------------
@bot.tree.command(name="setup", description="เปิดแผงปุ่มตั้งค่าระบบส่งข้อความแจ้งเตือน")
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ แผงควบคุมระบบแจ้งเตือน (Button Control)",
        description=(
            "**วิธีใช้งานง่ายๆ 2 ขั้นตอน:**\n\n"
            "1️⃣ กดปุ่ม **'📌 1. เลือกช่องที่จะส่ง'** แล้วเลือกห้องข้อความที่ต้องการ\n"
            "2️⃣ (ตัวเลือก) เลือก Emoji นำหน้าหัวข้อที่ต้องการ\n"
            "3️⃣ กดปุ่มสีเขียว **'📝 2. กรอกข้อมูล...'** เพื่อพิมพ์รายละเอียดและกดส่งประกาศ"
        ),
        color=discord.Color.blue(),
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
