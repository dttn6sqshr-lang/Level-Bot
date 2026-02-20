import discord
from discord.ext import commands
from discord import app_commands
import random
import time
import json
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not found!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

XP_COOLDOWN = 20
XP_MIN = 5
XP_MAX = 15

LEVEL_CHANNEL_NAME = "𖦹・🍄﹕bots！"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
xp_cooldowns = {}

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "xp": 0,
            "level": 1,
            "last_daily": None,
            "streak": 0
        }
    return data[user_id]

def xp_for_next(level):
    return level * 10

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot online")

@bot.event
async def on_member_remove(member):
    user_id = str(member.id)
    if user_id in data:
        del data[user_id]
        save_data(data)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    if user_id in xp_cooldowns and now - xp_cooldowns[user_id] < XP_COOLDOWN:
        return

    xp_cooldowns[user_id] = now
    user = get_user_data(user_id)

    gained = random.randint(XP_MIN, XP_MAX)
    user["xp"] += gained

    leveled_up = False
    while user["xp"] >= xp_for_next(user["level"]):
        user["xp"] -= xp_for_next(user["level"])
        user["level"] += 1
        leveled_up = True

    save_data(data)

    if leveled_up:
        for channel in message.guild.text_channels:
            if channel.name == LEVEL_CHANNEL_NAME:
                await channel.send(
                    f"""✨ Sweet Level Up!

{message.author.name} reached:
Level {user["level"]}

<:CC_heart:1474162033179230352> Keep chatting to grow sweeter 💗
"""
                )
                break

    await bot.process_commands(message)

# PROFILE
@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    user = get_user_data(interaction.user.id)
    bar_filled = int((user["xp"] / xp_for_next(user["level"])) * 10)
    bar = "<:CC_heart:1474162033179230352>" * bar_filled + "▢" * (10 - bar_filled)

    await interaction.response.send_message(
        f"""🍓 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐂𝐚𝐫𝐝

User: {interaction.user.name}

Level: {user["level"]}
XP: {user["xp"]} / {xp_for_next(user["level"])}

{bar}

🌸 Keep chatting to grow sweeter 🌸
""",
        ephemeral=True
    )

# LEADERBOARD
@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)[:5]

    lines = ""
    place = 1
    for uid, udata in sorted_users:
        member = interaction.guild.get_member(int(uid))
        name = member.name if member else "Unknown"

        lines += f"""<:CC_mascot_love:1474120644504322273>    :  #{place} {name}
Level {udata['level']} ・ {udata['xp']} XP

"""
        place += 1

    await interaction.response.send_message(
        f"""𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>

⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·

{lines}
<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!

🌸 Levels reset if you leave the server 🌸
"""
    )

# DAILY
@bot.tree.command(name="daily")
async def daily(interaction: discord.Interaction):
    user = get_user_data(interaction.user.id)
    now = datetime.utcnow()

    if user["last_daily"]:
        last = datetime.fromisoformat(user["last_daily"])
        if now - last < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last)
            h, rem = divmod(int(remaining.total_seconds()), 3600)
            m, _ = divmod(rem, 60)

            await interaction.response.send_message(
                f"""⏳ Too soon, sweetheart!

Come back in:
{h}h {m}m

Don’t break your streak 💔
""",
                ephemeral=True
            )
            return

        if now - last > timedelta(hours=48):
            user["streak"] = 0
            await interaction.response.send_message(
                """💔 Oh no…

Your daily streak has melted away  
But you can start fresh today 🌸
"""
            )

    user["streak"] += 1
    user["last_daily"] = now.isoformat()
    save_data(data)

    if user["streak"] % 7 == 0:
        await interaction.response.send_message(
            f"""🎀 Sweet Milestone!

You’ve reached a daily streak of:
{user["streak"]} days

Extra sweetness unlocked 🌸
"""
        )
    else:
        await interaction.response.send_message(
            f"""🌸 Daily Sweetness Claimed!

Streak: {user["streak"]} days

Come back tomorrow for more sweetness 💗
"""
        )

bot.run(TOKEN)