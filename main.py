import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import time
from datetime import datetime, timedelta

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

# ---------------- DATA ----------------

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

# ---------------- EVENTS ----------------

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
            "last_daily": "never"
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

        embed = discord.Embed(
            title="🧁 Level Up!",
            description=f"{message.author.mention} just leveled up!",
            color=0xF7C1D9
        )
        embed.add_field(name="New Level", value=f"Level {data[user_id]['level']}", inline=True)
        embed.add_field(name="Reward", value=f"+{reward} (Mimu)", inline=True)
        embed.set_thumbnail(url=message.author.display_avatar.url)

        level_channel = discord.utils.get(message.guild.text_channels, name=LEVEL_UP_CHANNEL_NAME)
        if level_channel:
            await level_channel.send(embed=embed)
            await level_channel.send(f"/modifybal add {message.author.mention} {reward}")

    save_data(data)
    await bot.process_commands(message)

# ---------------- BAR ----------------

def animated_bar(current, required, frames=10):
    filled = int((current / required) * frames)
    bar = BAR_EMOJI * filled + "▫" * (frames - filled)
    return bar

# ---------------- PROFILE ----------------

@bot.tree.command(name="profile", description="View your level profile")
async def profile(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data:
        await interaction.response.send_message("You have no profile yet!", ephemeral=True)
        return

    user = data[user_id]
    required_xp = user["level"] * 10
    bar = animated_bar(user["xp"], required_xp)

    embed = discord.Embed(title="🧾 User Receipt", color=0xF7C1D9)
    embed.add_field(name="User", value=interaction.user.mention, inline=True)
    embed.add_field(name="Level", value=user["level"], inline=True)
    embed.add_field(name="XP", value=f"{user['xp']} / {required_xp}", inline=False)
    embed.add_field(name="Progress", value=bar, inline=False)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# ---------------- LEADERBOARD ----------------

@bot.tree.command(name="leaderboard", description="Top 10 highest levels")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)[:10]

    desc = ""
    for i, (uid, info) in enumerate(sorted_users, start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else "Unknown"
        desc += f"**{i}.** {name} — Level {info['level']}\n"

    embed = discord.Embed(title="🏆 Level Leaderboard", description=desc, color=0xF7C1D9)
    await interaction.response.send_message(embed=embed)

# ---------------- DAILY ----------------

@bot.tree.command(name="daily", description="Claim daily reward")
async def daily(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data:
        await interaction.response.send_message("You have no profile yet!", ephemeral=True)
        return

    last = data[user_id]["last_daily"]

    if last != "never":
        last_time = datetime.fromisoformat(last)
        if datetime.now() - last_time < timedelta(days=1):
            remaining = timedelta(days=1) - (datetime.now() - last_time)
            await interaction.response.send_message(f"⏳ Come back in {remaining.seconds//3600}h!", ephemeral=True)
            return

    reward = random.randint(50, 100)
    data[user_id]["last_daily"] = datetime.now().isoformat()
    save_data(data)

    embed = discord.Embed(
        title="🎁 Daily Reward",
        description=f"You received **{reward} coins** (via Mimu)!",
        color=0xF7C1D9
    )

    await interaction.response.send_message(embed=embed)
    await interaction.channel.send(f"/modifybal add {interaction.user.mention} {reward}")

# ---------------- RUN ----------------

bot.run(TOKEN)