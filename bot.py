import discord
from discord.ext import commands
from discord import app_commands
import random
import sqlite3
import time
import os
import asyncio
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
    last_xp REAL
)""")
DB.commit()

XP_COOLDOWN = 20
REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"
BOT_CHANNEL_NAME = "𖦹・🍄﹕bots！"

COTTAGE_COLORS = [
    0xE8CFC4, 0xBFD8C2, 0xF2D7D9,
    0xDDE5B6, 0xD5C6E0, 0xF4E1D2
]

def get_color():
    return random.choice(COTTAGE_COLORS)

def get_user(user_id):
    CURSOR.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return CURSOR.fetchone()

def create_user(user_id):
    CURSOR.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, 0, 1, 0))
    DB.commit()

def needed_xp(level):
    return level * 10

def heart_bar(current, needed, frame=0):
    total = 10
    filled = int((current / needed) * total)
    hearts = []
    for i in range(total):
        if i < filled:
            hearts.append("<:CC_heart:1474162033179230352>")
        else:
            hearts.append("▫️")
    if filled < total:
        hearts[(frame % total)] = "💗"
    return "".join(hearts)

class LeaderboardView(discord.ui.View):
    def __init__(self, page=1):
        super().__init__(timeout=60)
        self.page = page

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await send_leaderboard(interaction, self.page, edit=True)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await send_leaderboard(interaction, self.page, edit=True)

async def send_leaderboard(interaction, page, edit=False):
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

    view = LeaderboardView(page)

    if edit:
        await interaction.response.edit_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot ready")

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
    if now - user[3] < XP_COOLDOWN:
        return

    xp_gain = random.randint(5, 15)
    if message.channel.name == REVIEW_CHANNEL_NAME:
        xp_gain = 50

    new_xp = user[1] + xp_gain
    level = user[2]
    need = needed_xp(level)

    CURSOR.execute("UPDATE users SET last_xp = ? WHERE user_id = ?", (now, message.author.id))

    if new_xp >= need:
        level += 1
        new_xp -= need
        CURSOR.execute("UPDATE users SET level = ?, xp = ? WHERE user_id = ?", (level, new_xp, message.author.id))
        DB.commit()

        channel = discord.utils.get(message.guild.text_channels, name=BOT_CHANNEL_NAME)
        if channel:
            reward = level
            embed = discord.Embed(
                title="✨ Level Up!",
                description=f"""**{message.author.name}** reached **Level {level}**

Reward: +{reward} balance  
<:CC_heart:1474162033179230352> Staff may now add the reward""",
                color=get_color()
            )
            await channel.send(embed=embed)
    else:
        CURSOR.execute("UPDATE users SET xp = ? WHERE user_id = ?", (new_xp, message.author.id))
        DB.commit()

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    data = get_user(user.id)
    if not data:
        await interaction.response.send_message("No profile yet.")
        return

    xp, level = data[1], data[2]
    need = needed_xp(level)

    embed = discord.Embed(
        title="🍓 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐂𝐚𝐫𝐝",
        description=f"""User: {user.name}

Level: {level}
XP: {xp} / {need}

{heart_bar(xp, need)}

🌸 Keep chatting to grow sweeter 🌸""",
        color=get_color()
    )
    msg = await interaction.response.send_message(embed=embed, fetch_response=True)

    for i in range(10):
        await asyncio.sleep(0.5)
        embed.description = f"""User: {user.name}

Level: {level}
XP: {xp} / {need}

{heart_bar(xp, need, i)}

🌸 Keep chatting to grow sweeter 🌸"""
        await msg.edit(embed=embed)

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await send_leaderboard(interaction, 1)

bot.run(TOKEN)