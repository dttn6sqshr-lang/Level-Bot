import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

db = sqlite3.connect("levels.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER,
    level INTEGER
)
""")
db.commit()

# ---------------- COLORS ----------------
def cottage_color():
    return discord.Color(int(random.choice([
        "F7C1CC","E8D5C4","C1E1C1","F3E5AB","D7BDE2","BEE7E8"
    ]),16))

# ---------------- XP MATH ----------------
def xp_needed(level):
    return level * 10

def heart_bar(xp, need):
    filled = int((xp / need) * 10)
    return "<:CC_heart:1474162033179230352>" * filled + "♡" * (10-filled)

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    data = cur.fetchone()
    if not data:
        cur.execute("INSERT INTO users VALUES (?,0,1)", (uid,))
        db.commit()
        return (uid,0,1)
    return data

# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot ready")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    uid,xp,level = get_user(message.author.id)
    gain = random.randint(5,15)
    xp += gain
    need = xp_needed(level)

    if xp >= need:
        xp -= need
        level += 1
        reward = level * 10

        channel = discord.utils.get(message.guild.channels, name="𖦹・🍄﹕bots！")

        embed = discord.Embed(
            description=f"""
🍰 {message.author.mention} reached **Level {level}**!

Reward: **{reward} Sugar Bits**
Staff may now add balance manually.
""",
            color=cottage_color()
        )
        await channel.send(embed=embed)

    cur.execute("UPDATE users SET xp=?, level=? WHERE user_id=?",(xp,level,message.author.id))
    db.commit()

# ---------------- RANK ----------------
@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    uid,xp,level = get_user(interaction.user.id)
    need = xp_needed(level)
    bar = heart_bar(xp,need)

    embed = discord.Embed(
        description=f"""
## 🍓 {interaction.user.name}'s Profile

Level **{level}**  
XP **{xp}/{need}**

{bar}

🌸 Levels reset if you leave the server 🌸
""",
        color=cottage_color()
    )
    await interaction.response.send_message(embed=embed)

# ---------------- LEADERBOARD ----------------
class LeaderboardView(discord.ui.View):
    def __init__(self,page=0):
        super().__init__(timeout=None)
        self.page=page

    async def build(self):
        cur.execute("SELECT user_id,level,xp FROM users ORDER BY level DESC,xp DESC")
        rows=cur.fetchall()
        start=self.page*5
        end=start+5
        chunk=rows[start:end]

        text="## 𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>\n\n⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·\n\n"

        for i,row in enumerate(chunk,start=start+1):
            user=await bot.fetch_user(row[0])
            text+=f"""<:CC_mascot_love:1474120644504322273>    :  #{i} {user.name}
Level {row[1]} ・ {row[2]} XP\n\n"""

        text+="<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!\n\n-# 🌸 Levels reset if you leave the server 🌸"

        return discord.Embed(description=text,color=cottage_color())

    @discord.ui.button(label="⬅")
    async def back(self,interaction:discord.Interaction,button:discord.ui.Button):
        if self.page>0:
            self.page-=1
        await interaction.response.edit_message(embed=await self.build(),view=self)

    @discord.ui.button(label="➡")
    async def next(self,interaction:discord.Interaction,button:discord.ui.Button):
        self.page+=1
        await interaction.response.edit_message(embed=await self.build(),view=self)

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    view=LeaderboardView()
    embed=await view.build()
    await interaction.response.send_message(embed=embed,view=view)

# ---------------- RUN ----------------
bot.run(TOKEN)