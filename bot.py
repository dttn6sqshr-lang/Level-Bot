import discord
from discord.ext import commands
import random
import sqlite3
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB = sqlite3.connect("levels.db")
CURSOR = DB.cursor()
CURSOR.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER,
    level INTEGER,
    last_xp INTEGER
)""")
DB.commit()

XP_COOLDOWN = 20
REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"
BOT_CHANNEL_NAME = "𖦹・🍄﹕bots！"

COTTAGE_COLORS = [
    0xC7B7A3, 0xE8CFC4, 0xBFD8C2,
    0xF2D7D9, 0xD5C6E0, 0xDDE5B6
]

def get_color():
    return random.choice(COTTAGE_COLORS)

def heart_bar(current, needed):
    total_hearts = 10
    filled = int((current / needed) * total_hearts)
    return "<:CC_heart:1474162033179230352>" * filled + "▢" * (total_hearts - filled)

def get_user(user_id):
    CURSOR.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return CURSOR.fetchone()

def create_user(user_id):
    CURSOR.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, 0, 1, 0))
    DB.commit()

@bot.event
async def on_ready():
    print("Bot online")

@bot.event
async def on_member_remove(member):
    CURSOR.execute("DELETE FROM users WHERE user_id = ?", (member.id,))
    DB.commit()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user = get_user(message.author.id)
    if not user:
        create_user(message.author.id)
        user = get_user(message.author.id)

    now = time.time()
    last_xp = user[3]

    if now - last_xp < XP_COOLDOWN:
        return

    xp_gain = random.randint(5, 15)
    if message.channel.name == REVIEW_CHANNEL_NAME:
        xp_gain = 50

    new_xp = user[1] + xp_gain
    level = user[2]
    needed = level * 10

    CURSOR.execute("UPDATE users SET last_xp = ? WHERE user_id = ?", (now, message.author.id))

    if new_xp >= needed:
        level += 1
        new_xp -= needed
        CURSOR.execute("UPDATE users SET level = ?, xp = ? WHERE user_id = ?", (level, new_xp, message.author.id))
        DB.commit()

        bot_channel = discord.utils.get(message.guild.text_channels, name=BOT_CHANNEL_NAME)
        if bot_channel:
            embed = discord.Embed(
                title="✨ Sweet Level Up!",
                description=f"""**{message.author.name}** reached:
Level {level}

Reward: +{level} balance

<:CC_heart:1474162033179230352> Staff may now add the reward""",
                color=get_color()
            )
            await bot_channel.send(embed=embed)
    else:
        CURSOR.execute("UPDATE users SET xp = ? WHERE user_id = ?", (new_xp, message.author.id))
        DB.commit()

    await bot.process_commands(message)

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    data = get_user(user.id)
    if not data:
        await interaction.response.send_message("No profile yet.")
        return

    xp, level = data[1], data[2]
    needed = level * 10

    embed = discord.Embed(
        title="🍓 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐂𝐚𝐫𝐝",
        description=f"""User: {user.name}

Level: {level}
XP: {xp} / {needed}

{heart_bar(xp, needed)}

🌸 Keep chatting to grow sweeter 🌸""",
        color=get_color()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction, page: int = 1):
    per_page = 5
    offset = (page - 1) * per_page

    CURSOR.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT ? OFFSET ?", (per_page, offset))
    rows = CURSOR.fetchall()

    desc = ""
    rank = offset + 1
    for user_id, level, xp in rows:
        user = await bot.fetch_user(user_id)
        desc += f"""<:CC_mascot_love:1474120644504322273>    :  #{rank} {user.name}
Level {level} ・ {xp} XP\n\n"""
        rank += 1

    embed = discord.Embed(
        title="## 𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>",
        description=desc + "<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!\n\n-# 🌸 Levels reset if you leave the server 🌸",
        color=get_color()
    )

    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)