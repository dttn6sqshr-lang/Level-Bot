import discord
from discord.ext import commands
from discord import app_commands
import random, json, math, asyncio

TOKEN = "YOUR_TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

COTTAGE_COLORS = [0xF7C5CC,0xFFE5B4,0xEEDC82,0xC1E1C1,0xF3D1F4,0xFFD6E0]
HEART_FULL = "<:CC_heart:1474162033179230352>"
HEART_EMPTY = "🤍"


# ---------- DATA ----------

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"xp": 0, "level": 1, "sugar": 0}
    return data[uid]

def xp_needed(level):
    return level * 10 + 100


# ---------- HEART BAR ----------

def heart_bar(xp, need):
    filled = int((xp / need) * 10)
    return HEART_FULL * filled + HEART_EMPTY * (10 - filled)


# ---------- XP ----------

async def add_xp(interaction, amount):
    user = get_user(interaction.user.id)
    user["xp"] += amount
    need = xp_needed(user["level"])

    if user["xp"] >= need:
        user["xp"] -= need
        user["level"] += 1

        reward = user["level"] * 5
        user["sugar"] += reward

        embed = discord.Embed(
            title="🌸 Level Up!",
            description=f"{interaction.user.mention} has reached **Level {user['level']}**!\n\n"
                        f"**Reward:** `{reward}` Sugar Bits 🍬\n"
                        f"*Staff can now add balance manually*",
            color=random.choice(COTTAGE_COLORS)
        )

        await interaction.channel.send(embed=embed)

    save_data()


# ---------- READY ----------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Ready!")


# ---------- REVIEW XP ----------

@bot.tree.command(name="review")
async def review(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    await add_xp(interaction, 15)

    embed = discord.Embed(
        title="📝 New Review",
        description=text,
        color=random.choice(COTTAGE_COLORS)
    )
    await interaction.followup.send(embed=embed)


# ---------- PROFILE ----------

@bot.tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    need = xp_needed(user["level"])

    embed = discord.Embed(
        title=f"🌸 {interaction.user.name}'s Profile",
        color=random.choice(COTTAGE_COLORS)
    )

    embed.description = (
        f"**Level:** {user['level']}\n"
        f"**XP:** {user['xp']} / {need}\n"
        f"**Heart Bar:**\n{heart_bar(user['xp'], need)}"
    )

    await interaction.response.send_message(embed=embed)


# ---------- LEADERBOARD VIEW ----------

class LeaderboardView(discord.ui.View):
    def __init__(self, users, page=0):
        super().__init__(timeout=60)
        self.users = users
        self.page = page

    def embed(self):
        start = self.page * 5
        end = start + 5
        chunk = self.users[start:end]

        desc = "## 𝐋𝐞𝐯𝐞𝐥 𝐋𝐞𝐚𝐝𝐞𝐫𝐛𝐨𝐚𝐫𝐝 <:CC_bell:1474449952087216199>\n\n"
        desc += "⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·⠀ ⠀  ·\n\n"

        for i,(uid,info) in enumerate(chunk, start=start+1):
            desc += f"<:CC_mascot_love:1474120644504322273>    :  #{i} {bot.get_user(int(uid)).name}\n"
            desc += f"Level {info['level']} ・ {info['xp']} XP\n\n"

        desc += "<:CC_heart:1474162033179230352>  Keep chatting to climb the sweetness ladder!\n"
        desc += "-# 🌸 Levels reset if you leave the server 🌸"

        return discord.Embed(description=desc, color=random.choice(COTTAGE_COLORS))

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if (self.page+1)*5 < len(self.users):
            self.page += 1
        await interaction.response.edit_message(embed=self.embed(), view=self)


# ---------- LEADERBOARD ----------

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_users = sorted(data.items(), key=lambda x: x[1]["level"], reverse=True)
    view = LeaderboardView(sorted_users)
    await interaction.response.send_message(embed=view.embed(), view=view)


bot.run(TOKEN)