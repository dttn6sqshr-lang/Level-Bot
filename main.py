import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import time

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not found!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

LEVEL_UP_CHANNEL_NAME = "𖦹・🍄﹕bots！"
REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"
DATA_FILE = "levels.json"

XP_MIN = 5
XP_MAX = 15
COOLDOWN = 20

BAR_EMOJI = "<:CC_heart:1474162033179230352>"

# ------------------ DATA ------------------

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_cooldowns = {}

# ------------------ EVENTS ------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} online")

@bot.event
async def on_member_remove(member):
    data = load_data()
    if str(member.id) in data:
        del data[str(member.id)]
        save_data(data)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    user_id = str(message.author.id)

    now = time.time()
    if user_id in user_cooldowns and now - user_cooldowns[user_id] < COOLDOWN:
        return

    user_cooldowns[user_id] = now

    if user_id not in data:
        data[user_id] = {
            "xp": 0,
            "level": 1,
            "currency": 0,
            "customer_number": len(data) + 1
        }

    xp_gain = random.randint(XP_MIN, XP_MAX)

    if message.channel.name == REVIEW_CHANNEL_NAME:
        xp_gain += 50

    data[user_id]["xp"] += xp_gain

    level = data[user_id]["level"]
    required_xp = level * 10

    if data[user_id]["xp"] >= required_xp:
        data[user_id]["xp"] -= required_xp
        data[user_id]["level"] += 1
        reward = data[user_id]["level"] * 10
        data[user_id]["currency"] += reward

        embed = discord.Embed(
            title="🧁 Level Up!",
            description=f"{message.author.mention} just leveled up!",
            color=0xF7C1D9
        )
        embed.add_field(name="New Level", value=f"Level {data[user_id]['level']}", inline=True)
        embed.add_field(name="Reward", value=f"+{reward} coins", inline=True)
        embed.set_thumbnail(url=message.author.display_avatar.url)

        level_channel = discord.utils.get(message.guild.text_channels, name=LEVEL_UP_CHANNEL_NAME)
        if level_channel:
            await level_channel.send(embed=embed)

    save_data(data)
    await bot.process_commands(message)

# ------------------ BAR ------------------

def make_bar(current, required, length=10):
    filled = int((current / required) * length)
    return BAR_EMOJI * filled + "▫" * (length - filled)

# ------------------ SLASH COMMAND ------------------

@bot.tree.command(name="profile", description="View your level profile")
async def profile(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data:
        await interaction.response.send_message("You have no profile yet!", ephemeral=True)
        return

    user = data[user_id]
    required_xp = user["level"] * 10
    bar = make_bar(user["xp"], required_xp)

    embed = discord.Embed(
        title="🧾 Customer Receipt",
        color=0xF7C1D9
    )
    embed.add_field(name="Customer #", value=user["customer_number"], inline=True)
    embed.add_field(name="Level", value=user["level"], inline=True)
    embed.add_field(name="XP", value=f"{user['xp']} / {required_xp}", inline=False)
    embed.add_field(name="Progress", value=bar, inline=False)
    embed.add_field(name="Balance", value=f"{user['currency']} coins", inline=True)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# ------------------ RUN ------------------

bot.run(TOKEN)