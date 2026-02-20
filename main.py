import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import time
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

XP_COOLDOWN = 20
LEVEL_CHANNEL_NAME = "𖦹・🍄﹕bots！"
REVIEW_CHANNEL = "✿﹒⤷﹒﹒﹒reviews"

DATA_FILE = "levels.json"
DAILY_FILE = "daily.json"

# ----------------- DATA -----------------

def load_data(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

levels = load_data(DATA_FILE)
daily = load_data(DAILY_FILE)
cooldowns = {}

# ----------------- LEVEL FUNCTIONS -----------------

def get_xp_needed(level):
    return level * 10

def create_user(user_id):
    if str(user_id) not in levels:
        levels[str(user_id)] = {"xp": 0, "level": 1}

def make_bar(xp, needed, size=10):
    filled = int((xp / needed) * size)
    return "<:CC_heart:1474162033179230352>" * filled + "▢" * (size - filled)

# ----------------- EVENTS -----------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_remove(member):
    if str(member.id) in levels:
        del levels[str(member.id)]
        save_data(DATA_FILE, levels)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = time.time()

    if user_id in cooldowns and now - cooldowns[user_id] < XP_COOLDOWN:
        return

    cooldowns[user_id] = now
    create_user(user_id)

    xp_gain = random.randint(5, 15)
    levels[user_id]["xp"] += xp_gain

    while levels[user_id]["xp"] >= get_xp_needed(levels[user_id]["level"]):
        levels[user_id]["xp"] -= get_xp_needed(levels[user_id]["level"])
        levels[user_id]["level"] += 1

        for channel in message.guild.text_channels:
            if channel.name == LEVEL_CHANNEL_NAME:
                embed = discord.Embed(
                    title="✨ Level Up! ✨",
                    description=f"**{message.author.name}** reached **Level {levels[user_id]['level']}**!",
                    color=0xffc0cb
                )
                await channel.send(embed=embed)

    save_data(DATA_FILE, levels)
    await bot.process_commands(message)

# ----------------- PROFILE -----------------

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    create_user(user_id)

    xp = levels[user_id]["xp"]
    level = levels[user_id]["level"]
    needed = get_xp_needed(level)
    bar = make_bar(xp, needed)

    embed = discord.Embed(title="🍓 Profile Card", color=0xffb6c1)
    embed.add_field(name="User", value=interaction.user.name, inline=False)
    embed.add_field(name="Level", value=f"{level}", inline=True)
    embed.add_field(name="XP", value=f"{xp}/{needed}", inline=True)
    embed.add_field(name="Progress", value=bar, inline=False)

    await interaction.response.send_message(embed=embed)

# ----------------- LEADERBOARD -----------------

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(levels.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)

    desc = "⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·\n\n"

    for i, (user_id, data) in enumerate(sorted_users[:5], start=1):
        user = await bot.fetch_user(int(user_id))
        desc += f"<:CC_mascot_love:1474120644504322273>    :  #{i} {user.name}\n"
        desc += f"Level {data['level']} ・ {data['xp']} XP\n\n"

    desc += "<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!\n\n🌸 Levels reset if you leave the server 🌸"

    embed = discord.Embed(
        title="𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>",
        description=desc,
        color=0xffc0cb
    )

    await interaction.response.send_message(embed=embed)

# ----------------- DAILY -----------------

@bot.tree.command(name="daily")
async def daily_cmd(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.utcnow()

    if user_id not in daily:
        daily[user_id] = {"last": str(now), "streak": 1}
        save_data(DAILY_FILE, daily)
        await interaction.response.send_message("🌸 Daily reward claimed! Streak: **1**")
        return

    last = datetime.fromisoformat(daily[user_id]["last"])
    diff = now - last

    if diff < timedelta(hours=24):
        remaining = timedelta(hours=24) - diff
        await interaction.response.send_message(f"⏳ Come back in **{remaining.seconds//3600}h {(remaining.seconds%3600)//60}m**!")
        return

    if diff > timedelta(hours=48):
        daily[user_id]["streak"] = 1
        msg = "💔 Your streak broke… Starting again!"
    else:
        daily[user_id]["streak"] += 1
        msg = f"🌸 Daily claimed! Streak: **{daily[user_id]['streak']}**"

    if daily[user_id]["streak"] % 7 == 0:
        msg += "\n🎁 **Bonus milestone reached!**"

    daily[user_id]["last"] = str(now)
    save_data(DAILY_FILE, daily)

    await interaction.response.send_message(msg)

# -----------------

bot.run(TOKEN)