import discord
from discord import app_commands
import random
import json
import os
import time
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")

XP_COOLDOWN = 20
REVIEW_CHANNEL = "✿﹒⤷﹒﹒﹒reviews"
LEVELUP_CHANNEL = "𖦹・🍄﹕bots！"

DATA_FILE = "levels.json"

HEART = "<:CC_heart:1474162033179230352>"
TROPHY = "<:CC_trophy:1474577678790299821>"
CHAT = "<:CC_chatbubble:1474578856144011338>"

COTTAGE_COLORS = [0xF7C8D4, 0xFFD6E8, 0xFDE2B8, 0xD7F2E3]

# ================= KEEP ALIVE =================
app = Flask("")
@app.route("/")
def home():
    return "alive"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# ================= BOT =================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# ================= DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
cooldowns = {}

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": 1,
            "messages": 0,
            "streak": 0,
            "last_msg": 0,
            "last_level": 0
        }
    return data[uid]

# ================= XP LOGIC =================
def xp_needed(level):
    return level * 120

def heart_bar(xp, need):
    filled = int((xp / need) * 5)
    return HEART * filled + "♡" * (5 - filled)

def reward_amount(level):
    return level * 5

# ================= READY =================
@bot.event
async def on_ready():
    await tree.sync()
    print("Level bot online")

# ================= MESSAGE XP =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user = get_user(message.author.id)
    now = time.time()

    if now - user["last_msg"] < XP_COOLDOWN:
        return

    user["last_msg"] = now
    user["messages"] += 1

    xp_gain = random.randint(4, 9)

    if message.channel.name == REVIEW_CHANNEL:
        xp_gain += 50

    # lucky XP
    if random.randint(1, 100) <= 5:
        xp_gain += random.randint(10, 30)
        await message.channel.send("🍀 Lucky XP Moment!")

    # fairy
    if random.randint(1, 100) <= 3:
        await message.channel.send("🧚 A fairy visited! +15 XP")
        xp_gain += 15

    user["xp"] += xp_gain

    need = xp_needed(user["level"])

    if user["xp"] >= need:
        user["xp"] -= need
        user["level"] += 1
        user["last_level"] = time.time()

        reward = reward_amount(user["level"])

        channel = discord.utils.get(message.guild.text_channels, name=LEVELUP_CHANNEL)
        if channel:
            await channel.send(
f"""_ _
      ∂𝜚       {message.author.mention}  ─
        ❤︎   LEVEL UP   ❤︎
_ _

{HEART*5}

You reached **Level {user['level']}**

Reward: **{reward} Sugar Bits** 🍬  
Staff can now add your balance!
"""
            )

    save_data()

# ================= PROFILE =================
@tree.command(name="profile")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    if not user:
        user = interaction.user

    u = get_user(user.id)
    need = xp_needed(u["level"])
    bar = heart_bar(u["xp"], need)

    embed = discord.Embed(
        title="🎀 Profile Card",
        color=random.choice(COTTAGE_COLORS)
    )

    embed.description = f"""
_ _
      ∂𝜚       {user.name} ─
        ❤︎   Level {u['level']}   ❤︎
_ _

{bar}

XP: {u['xp']} / {need}

{CHAT} Messages: {u['messages']}
{TROPHY} Rank: calculating...
💗 Streak: {u['streak']} days
⏰ Last Level Up: <t:{int(u['last_level'])}:R>
🍬 Sugar Bits Earned: {reward_amount(u['level'])}
"""

    await interaction.response.send_message(embed=embed)

# ================= LEADERBOARD =================
@tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)

    text = ""
    rank = 1
    for uid, u in sorted_users[:10]:
        member = interaction.guild.get_member(int(uid))
        if member:
            text += f"{TROPHY} #{rank} {member.name}\nLevel {u['level']} ・ {u['xp']} XP\n\n"
            rank += 1

    embed = discord.Embed(
        title="## 🌸 Level Leaderboard",
        description=text + f"{HEART} Keep chatting to climb the sweetness ladder!",
        color=random.choice(COTTAGE_COLORS)
    )

    await interaction.response.send_message(embed=embed)

# ================= RESET ON LEAVE =================
@bot.event
async def on_member_remove(member):
    if str(member.id) in data:
        del data[str(member.id)]
        save_data()

# ================= RUN =================
bot.run(TOKEN)