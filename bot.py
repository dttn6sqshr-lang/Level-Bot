import discord
from discord import app_commands
import random, json, os, time
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")

XP_COOLDOWN = 20
REVIEW_CHANNEL = "✿﹒⤷﹒﹒﹒reviews"
LEVELUP_CHANNEL = "𖦹・🍄﹕bots！"

DATA_FILE = "levels.json"

HEART = "<:CC_heart:1474162033179230352>"
TROPHY = "<:CC_trophy:1474577678790299821>"
CHAT = "<:CC_chatbubble:1474578856144011338>"

COTTAGE_COLORS = [0xFADADD, 0xFFF1C1, 0xE6F7E7, 0xF3D1F4]

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

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "level": 1,
            "messages": 0,
            "streak": 0,
            "last_msg": 0,
            "last_day": 0,
            "last_level": 0,
            "favorite_channel": "",
            "last_daily": 0
        }
    return data[uid]

# ================= XP LOGIC =================
def xp_needed(level):
    return int(200 + (level ** 1.5) * 60)

def heart_bar(xp, need):
    percent = xp / need
    filled = int(percent * 10)
    bar = HEART * filled + "♡" * (10 - filled)

    if percent >= 0.85:
        bar = "💗" + bar + "💗"

    return bar

def reward_amount(level):
    return level * 10

LEVEL_REWARDS = {4:50, 9:100, 27:250, 29:300}

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
    user["favorite_channel"] = message.channel.name

    xp_gain = random.randint(2, 5)

    if message.channel.name == REVIEW_CHANNEL:
        xp_gain += 50

    if random.randint(1, 100) <= 5:
        xp_gain += random.randint(15, 40)
        await message.channel.send("🍀 Lucky XP moment!")

    if random.randint(1, 100) <= 3:
        xp_gain += 20
        await message.channel.send("🧚 Fairy visited! +20 XP")

    today = datetime.utcnow().date()
    last_day = datetime.utcfromtimestamp(user["last_day"]).date() if user["last_day"] else None

    if last_day == today - timedelta(days=1):
        user["streak"] += 1
        xp_gain += min(user["streak"] * 2, 30)
    elif last_day != today:
        user["streak"] = 1

    user["last_day"] = time.time()
    user["xp"] += xp_gain

    need = xp_needed(user["level"])

    if user["xp"] >= need:
        user["xp"] -= need
        user["level"] += 1
        user["last_level"] = time.time()

        reward = reward_amount(user["level"])
        bonus = LEVEL_REWARDS.get(user["level"], 0)

        channel = discord.utils.get(message.guild.text_channels, name=LEVELUP_CHANNEL)
        if channel:
            await channel.send(
f"""_ _
      ∂𝜚       {message.author.mention}  ─
        ❤︎   LEVEL UP   ❤︎
_ _

{HEART*10}

You reached **Level {user['level']}**

Reward: **{reward} Sugar Bits** 🍬  
Bonus: **{bonus} Sugar Bits**

Staff can now add balance!
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

    embed = discord.Embed(title="🎀 Profile Card", color=random.choice(COTTAGE_COLORS))
    embed.description = f"""
_ _
      ∂𝜚       {user.name} 
        ❤︎   Level {u['level']}   ❤︎
_ _

{bar}

XP: {u['xp']} / {need}

{CHAT} Messages: {u['messages']}
Streak: {u['streak']} days
Last Level Up: <t:{int(u['last_level'])}:R>
Favorite Channel: {u['favorite_channel']}
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
        title=" 🌸 Level Leaderboard",
        description=text + f"{HEART} Keep chatting to climb the sweetness ladder!",
        color=random.choice(COTTAGE_COLORS)
    )

    await interaction.response.send_message(embed=embed)

# ================= DAILY =================
@tree.command(name="daily")
async def daily(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    now = time.time()

    if now - user["last_daily"] < 86400:
        remaining = int(86400 - (now - user["last_daily"]))
        await interaction.response.send_message(f"⏳ Try again in {remaining//3600}h", ephemeral=True)
        return

    user["last_daily"] = now
    reward = random.randint(50, 120)
    await interaction.response.send_message(f"🍬 Daily reward: **{reward} Sugar Bits**\nStaff can add it!")
    save_data()

# ================= RESET ON LEAVE =================
@bot.event
async def on_member_remove(member):
    if str(member.id) in data:
        del data[str(member.id)]
        save_data()

bot.run(TOKEN)