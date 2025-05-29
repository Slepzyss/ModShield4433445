import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import json

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for kick/ban actions
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

# Helper function to check mod/admin permissions
def is_mod():
    async def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions
        return perms.kick_members or perms.ban_members or perms.manage_messages or perms.administrator
    return app_commands.check(predicate)

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

# Kick command
@tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kick (optional)")
@is_mod()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member} was kicked from the server.")
        await log_mod_action(bot, "Kick", member, interaction.user, reason)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to kick this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# Ban command
@tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for ban (optional)")
@is_mod()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member} was banned from the server.")
        await log_mod_action(bot, "Ban", member, interaction.user, reason)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to ban this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# Warn command (just sends a DM warning)
@tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="The member to warn", reason="Reason for warning")
@is_mod()
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    try:
        await member.send(f"You have been warned in **{interaction.guild.name}** for: {reason}")
        await interaction.response.send_message(f"{member} has been warned.")
        await log_mod_action(bot, "Warn", member, interaction.user, reason)
    except discord.Forbidden:
        await interaction.response.send_message("I cannot send a DM to this member.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

# Purge command (deletes messages)
@tree.command(name="purge", description="Delete a number of messages")
@app_commands.describe(amount="Number of messages to delete (max 100)")
@is_mod()
async def purge(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("You must specify a number between 1 and 100.", ephemeral=True)
        return
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
        # Log purge without member, but include the moderator and amount
        guild_id = interaction.guild.id
        channel_id = modlog_channels.get(str(guild_id))
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(title="Moderation Action", color=discord.Color.red())
                embed.add_field(name="Action", value="Purge", inline=True)
                embed.add_field(name="Moderator", value=str(interaction.user), inline=True)
                embed.add_field(name="Amount", value=str(len(deleted)), inline=True)
                await channel.send(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("I do not have permission to delete messages.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
