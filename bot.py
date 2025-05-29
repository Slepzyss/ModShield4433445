import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import json

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

MODLOG_FILE = "modlog_channels.json"

def load_modlog_channels():
    try:
        with open(MODLOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_modlog_channels(data):
    with open(MODLOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

modlog_channels = load_modlog_channels()

@bot.event
async def on_ready():
    guild_count = len(bot.guilds)
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{guild_count} servers"
    )
    await bot.change_presence(activity=activity)

    try: 
        await tree.sync()
        print(f"🟢 Synced slash commands globally.")
    except Exception as e:
        print(f"🔴 Failed to sync slash commands globally: {e}")

    print(f"🟢 Logged in as {bot.user} | Watching {guild_count} servers | Synced slash commands.")

@tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@tree.command(name="setmodlog", description="Set the moderation log channel")
@app_commands.describe(channel="The channel to log moderation actions")
async def setmodlog(interaction: discord.Interaction, channel: discord.TextChannel):
    # Only allow server owner
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Only the server owner can set the mod-log channel.", ephemeral=True)
        return

    modlog_channels[str(interaction.guild.id)] = channel.id
    save_modlog_channels(modlog_channels)
    await interaction.response.send_message(f"Mod-log channel has been set to {channel.mention}")

async def log_mod_action(bot, action, member, moderator, reason=None):
    guild_id = member.guild.id
    channel_id = modlog_channels.get(str(guild_id))
    if not channel_id:
        return  # No mod log set for this guild
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(title="Moderation Action", color=discord.Color.red())
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Member", value=str(member), inline=True)
        embed.add_field(name="Moderator", value=str(moderator), inline=True)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await channel.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
