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
            print("✅ Sync Slash Commands successfully")
        except Exception as e:
            print(f"❌ Sync Error: {e}")


bot = NotificationBot()


class MessageModal(discord.ui.Modal, title="Set Notification Details"):
    title_input = discord.ui.TextInput(
        label="Title",
        style=discord.TextStyle.short,
        placeholder="Enter announcement title...",
        required=True,
        max_length=100,
    )

    message_input = discord.ui.TextInput(
        label="Message Content",
        style=discord.TextStyle.paragraph,
        placeholder="Enter announcement details...",
        required=True,
        max_length=2000,
    )

    image_url_input = discord.ui.TextInput(
        label="Image Banner URL (Optional)",
        style=discord.TextStyle.short,
        placeholder="https://...png or jpg",
        required=False,
    )

    button_label_input = discord.ui.TextInput(
        label="Website Button Name (Optional)",
        style=discord.TextStyle.short,
        placeholder="e.g. Visit Website",
        required=False,
        max_length=80,
    )

    button_url_input = discord.ui.TextInput(
        label="Website URL (Optional)",
        style=discord.TextStyle.short,
        placeholder="https://your-website.com",
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not bot.selected_channel_id:
            await interaction.response.send_message(
                "❌ Please select a channel first!", ephemeral=True
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
                text=f"Announced by {interaction.user.display_name}",
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
                    f"✅ Sent notification to {channel.mention} successfully!",
                    ephemeral=True,
                )
            except Exception as err:
                await interaction.response.send_message(
                    f"❌ Failed to send message: {err}",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(
                "❌ Selected channel not found.", ephemeral=True
            )


class SetupView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="📌 1. Select Channel...",
        row=0,
    )
    async def select_channel(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        bot.selected_channel_id = select.values[0].id
        selected_channel = select.values[0]
        await interaction.response.send_message(
            f"✅ Selected channel **#{selected_channel.name}**!",
            ephemeral=True,
        )

    @discord.ui.select(
        placeholder="😀 2. Select Emoji (Default: 📢)",
        options=[
            discord.SelectOption(label="Cart / Shop", value="🛒", emoji="🛒"),
            discord.SelectOption(label="Announcement", value="📢", emoji="📢"),
            discord.SelectOption(label="Warning", value="⚠️", emoji="⚠️"),
            discord.SelectOption(label="Event / Party", value="🎉", emoji="🎉"),
            discord.SelectOption(label="Fire / Hot", value="🔥", emoji="🔥"),
            discord.SelectOption(label="Info / Tips", value="💡", emoji="💡"),
            discord.SelectOption(label="Website / Link", value="🌐", emoji="🌐"),
        ],
        row=1,
    )
    async def select_emoji(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        bot.selected_emoji = select.values[0]
        await interaction.response.send_message(
            f"✅ Selected Emoji: {bot.selected_emoji}", ephemeral=True
        )

    @discord.ui.button(
        label="📝 3. Enter Details & Banner & Website",
        style=discord.ButtonStyle.green,
        row=2,
    )
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not bot.selected_channel_id:
            await interaction.response.send_message(
                "⚠️ Please select a channel first!",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(MessageModal())


@bot.tree.command(
    name="setup",
    description="Setup notification system",
)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ Notification Setup System",
        description=(
            "**Follow steps below to make an announcement:**\n\n"
            "1️⃣ **Select Channel:** Choose where to send\n"
            "2️⃣ **Select Emoji:** Choose prefix icon\n"
            "3️⃣ **Enter Details:** Click green button to fill text, image, website"
        ),
        color=discord.Color.blue(),
    )
    await interaction.response.send_message(
        embed=embed, view=SetupView(), ephemeral=True
    )


@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user.name}")


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ DISCORD_TOKEN missing in environment variables.")
else:
    bot.run(TOKEN.strip())
