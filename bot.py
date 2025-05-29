import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

tree = bot.tree

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

TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)