import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
import time

TOKEN = "YOUR_TOKEN_HERE"

REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"
BOT_CHANNEL_NAME = "𖦹・🍄﹕bots！"

XP_COOLDOWN = 20
MIN_XP = 5
MAX_XP = 15
REVIEW_BONUS = 50

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

db = sqlite3.connect("levels.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER,
    level INTEGER,
    last_xp REAL,
    last_daily INTEGER,
    streak INTEGER
)
""")
db.commit()

def get_color():
    colors = [0xC1E1C1, 0xFFD1DC, 0xEAD7C5, 0xB5EAD7, 0xFFF1C1]
    return random.choice(colors)

def heart_bar(xp, need):
    filled = int((xp / need) * 10)
    empty = 10 - filled
    return "<:CC_heart:1474162033179230352>" * filled + "🤍" * empty

def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    data = cursor.fetchone()
    if not data:
        cursor.execute(
            "INSERT INTO users VALUES (?, 0, 1, 0, 0, 0)",
            (uid,)
        )
        db.commit()
        return (uid, 0, 1, 0, 0, 0)
    return data

@bot.event
async def on_ready():
    await tree.sync()
    print("Bot ready")

@bot.event
async def on_member_remove(member):
    cursor.execute("DELETE FROM users WHERE user_id = ?", (member.id,))
    db.commit()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id, xp, level, last_xp, last_daily, streak = get_user(message.author.id)

    now = time.time()
    if now - last_xp < XP_COOLDOWN:
        return

    gain = random.randint(MIN_XP, MAX_XP)
    if message.channel.name == REVIEW_CHANNEL_NAME:
        gain += REVIEW_BONUS

    new_xp = xp + gain
    need = level * 10

    leveled = False

    if new_xp >= need:
        level += 1
        new_xp -= need
        leveled = True

    cursor.execute("""
    UPDATE users SET xp=?, level=?, last_xp=? WHERE user_id=?
    """, (new_xp, level, now, message.author.id))
    db.commit()

    if leveled:
        channel = discord.utils.get(message.guild.text_channels, name=BOT_CHANNEL_NAME)
        if channel:
            reward = level
            embed = discord.Embed(
                title="✨ Level Up!",
                description=(
                    f"{message.author.mention} reached **Level {level}**\n\n"
                    f"🎀 Reward: **+{reward} Sugar Bits**\n"
                    "Staff may now add balance"
                ),
                color=get_color()
            )
            await channel.send(embed=embed)

@tree.command(name="profile")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    if not user:
        user = interaction.user

    user_id, xp, level, last_xp, last_daily, streak = get_user(user.id)
    need = level * 10

    bar = heart_bar(xp, need)

    embed = discord.Embed(
        title=f"{user.name}'s Profile",
        description=(
            f"**Level:** {level}\n"
            f"**XP:** {xp}/{need}\n\n"
            f"{bar}"
        ),
        color=get_color()
    )
    await interaction.response.send_message(embed=embed)

class LeaderboardView(discord.ui.View):
    def __init__(self, page=0):
        super().__init__(timeout=60)
        self.page = page

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.update(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update(interaction)

    async def update(self, interaction):
        cursor.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC")
        rows = cursor.fetchall()

        start = self.page * 5
        end = start + 5
        page_rows = rows[start:end]

        if not page_rows:
            self.page = 0
            start = 0
            end = 5
            page_rows = rows[start:end]

        text = ""
        for i, row in enumerate(page_rows, start=start + 1):
            user = interaction.guild.get_member(row[0])
            name = user.name if user else "User"
            text += (
                f"<:CC_mascot_love:1474120644504322273>    :  #{i} {name}\n"
                f"Level {row[1]} ・ {row[2]} XP\n\n"
            )

        embed = discord.Embed(
            title="## 𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>",
            description=(
                "⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·\n\n"
                + text +
                "<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!\n\n"
                "-# 🌸 Levels reset if you leave the server 🌸"
            ),
            color=get_color()
        )

        await interaction.response.edit_message(embed=embed, view=self)

@tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    view = LeaderboardView()
    await view.update(interaction)

@tree.command(name="daily")
async def daily(interaction: discord.Interaction):
    user_id, xp, level, last_xp, last_daily, streak = get_user(interaction.user.id)

    now = int(time.time())
    if now - last_daily < 86400:
        embed = discord.Embed(
            title="Daily Reward",
            description="⏳ You already claimed today!",
            color=get_color()
        )
        await interaction.response.send_message(embed=embed)
        return

    if now - last_daily > 172800:
        streak = 0

    streak += 1
    reward = 50 + (streak * 10)

    cursor.execute("""
    UPDATE users SET last_daily=?, streak=? WHERE user_id=?
    """, (now, streak, interaction.user.id))
    db.commit()

    embed = discord.Embed(
        title="Daily Reward",
        description=(
            f"🎁 You claimed **{reward} Sugar Bits**\n"
            f"🔥 Streak: {streak}"
        ),
        color=get_color()
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)