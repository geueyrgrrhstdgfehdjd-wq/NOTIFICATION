import os
import sys
import asyncio
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

# ------------------------------------------
# แก้ไขปัญหา Event Loop บน Python เวอร์ชันใหม่ๆ
# ------------------------------------------
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
            print(f"❌ เกิดข้อผิดพลาดในการซิงค์ Slash Commands: {e}")


bot = NotificationBot()


# ------------------------------------------
# 1. หน้าต่าง Modal สำหรับกรอกข้อมูลแจ้งเตือน
# ------------------------------------------
class MessageModal(discord.ui.Modal, title="ตั้งค่าข้อความ รูปภาพ และเว็บไซต์"):
    title_input = discord.ui.TextInput(
        label="หัวข้อประกาศ",
        style=discord.TextStyle.short,
        placeholder="เช่น โปรโมชั่นพิเศษประจำเดือน / แจ้งเตือนปิดปรับปรุง",
        required=True,
        max_length=100,
    )

    message_input = discord.ui.TextInput(
        label="เนื้อหาข้อความแจ้งเตือน",
        style=discord.TextStyle.paragraph,
        placeholder="รายละเอียดข้อความที่ต้องการแจ้งเตือน...",
        required=True,
        max_length=2000,
    )

    image_url_input = discord.ui.TextInput(
        label="ลิงก์รูปแบนเนอร์ (ถ้าไม่มีให้เว้นว่างไว้)",
        style=discord.TextStyle.short,
        placeholder="https://...png หรือ jpg",
        required=False,
    )

    button_label_input = discord.ui.TextInput(
        label="ชื่อปุ่มเว็บไซต์ (ถ้ามี)",
        style=discord.TextStyle.short,
        placeholder="เช่น เข้าสู่เว็บไซต์ / สั่งซื้อสินค้า",
        required=False,
        max_length=80,
    )

    button_url_input = discord.ui.TextInput(
        label="URL เว็บไซต์ (ต้องเริ่มด้วย http:// หรือ https://)",
        style=discord.TextStyle.short,
        placeholder="https://your-website.com",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not bot.selected_channel_id:
            await interaction.response.send_message(
                "❌ กรุณาเลือกช่องที่จะแจ้งเตือนก่อนครับ!", ephemeral=True
            )
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

            out_view = None
            if self.button_url_input.value and self.button_label_input.value:
                url = self.button_url_input.value.strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url

                out_view = discord.ui.View()
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

                await interaction.response.send_message(
                    f"✅ ส่งประกาศไปยังช่อง {channel.mention} เรียบร้อยแล้ว!",
                    ephemeral=True,
                )
            except Exception as err:
                await interaction.response.send_message(
                    f"❌ ไม่สามารถส่งข้อความได้ โปรดตรวจสอบสิทธิ์การส่งข้อความของบอท: {err}",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "❌ ไม่พบช่องที่เลือก กรุณาเลือกช่องใหม่อีกครั้ง", ephemeral=True
            )


# ------------------------------------------
# 2. เมนูและปุ่มกดตั้งค่า (UI Components)
# ------------------------------------------
class SetupView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="📌 1. เลือกช่องที่จะให้ส่งข้อความแจ้งเตือน...",
        row=0,
    )
    async def select_channel(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        bot.selected_channel_id = select.values[0].id
        selected_channel = select.values[0]
        await interaction.response.send_message(
            f"✅ เลือกช่อง **#{selected_channel.name}** เรียบร้อยแล้ว!",
            ephemeral=True,
        )

    @discord.ui.select(
        placeholder="😀 2. เลือก Emoji นำหน้าหัวข้อ (ค่าเริ่มต้น: 📢)",
        options=[
            discord.SelectOption(label="รถเข็น / สินค้า", value="🛒", emoji="🛒"),
            discord.SelectOption(label="ประกาศ / ข่าวสาร", value="📢", emoji="📢"),
            discord.SelectOption(label="เตือนภัย / ข้อควรระวัง", value="⚠️", emoji="⚠️"),
            discord.SelectOption(label="กิจกรรม / ฉลอง", value="🎉", emoji="🎉"),
            discord.SelectOption(label="ไฟ / ฮอตฮิต", value="🔥", emoji="🔥"),
            discord.SelectOption(label="ข้อมูล / คำแนะนำ", value="💡", emoji="💡"),
            discord.SelectOption(label="เว็บไซต์ / ลิงก์", value="🌐", emoji="🌐"),
        ],
        row=1,
    )
    async def select_emoji(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        bot.selected_emoji = select.values[0]
        await interaction.response.send_message(
            f"✅ เลือก Emoji เป็น: {bot.selected_emoji}", ephemeral=True
        )

    @discord.ui.button(
        label="📝 3. กรอกรายละเอียดข้อความ & รูป & Website",
        style=discord.ButtonStyle.green,
        row=2,
    )
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not bot.selected_channel_id:
            await interaction.response.send_message(
                "⚠️ กรุณาเลือกช่องที่ต้องการส่งข้อความในดรอปดาวน์ก่อนครับ",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(MessageModal())


# ------------------------------------------
# 3. คำสั่ง Slash Command: /setup
# ------------------------------------------
@bot.tree.command(
    name="setup",
    description="ตั้งค่าระบบแจ้งเตือน (เลือกช่อง, Emoji, ข้อความ, รูป และปุ่ม Website)",
)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ ระบบจัดทำข้อความแจ้งเตือนอัตโนมัติ",
        description=(
            "**กรุณาทำตามขั้นตอนด้านล่างเพื่อสร้างประกาศ:**\n\n"
            "1️⃣ **เลือกช่อง (Channel):** เลือกห้องที่ต้องการให้บอทไปส่งประกาศ\n"
            "2️⃣ **เลือก Emoji:** เลือกสัญลักษณ์ที่จะวางไว้หน้าหัวข้อประกาศ\n"
            "3️⃣ **กรอกข้อมูล:** กดปุ่มสีเขียวเพื่อกรอกหัวข้อ, เนื้อหา, ลิงก์รูปแบนเนอร์"
            " และปุ่มลิงก์ Website"
        ),
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(
        embed=embed, view=SetupView(), ephemeral=True
    )


@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"✅ บอทแจ้งเตือนออนไลน์เรียบร้อยแล้ว!")
    print(f"🤖 ชื่อบอท: {bot.user.name} (ID: {bot.user.id})")
    print("--------------------------------------------------")


# ------------------------------------------
# ส่วนการเริ่มรันบอทและแจ้งการเชื่อมต่อ
# ------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ [ERROR]: ไม่พบ DISCORD_TOKEN ใน Environment Variables")
    print("👉 กรุณาตรวจสอบในเมนู Env อีกครั้งว่าตั้ง KEY เป็น 'DISCORD_TOKEN' หรือไม่")
else:
    try:
        print("🔄 กำลังเชื่อมต่อกับ Discord...")
        bot.run(TOKEN.strip())
    except discord.errors.LoginFailure:
        print("❌ [ERROR]: Token ไม่ถูกต้อง (LoginFailure)")
        print("👉 กรุณาไป Reset Token ใหม่ใน Discord Developer Portal แล้วนำมาใส่ใหม่")
    except Exception as e:
        print(f"❌ [ERROR]: เกิดข้อผิดพลาดตอนเริ่มรันบอท: {e}")
