import discord
from discord import app_commands
import random, json, os, time
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")

REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"
DATA_FILE = "levels.json"
XP_COOLDOWN = 20

HEART = "<:CC_heart:1474162033179230352>"

# ================= KEEP ALIVE =================
app = Flask("")

@app.route("/")
def home():
    return "Level bot alive!"

Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()

# ================= BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

cooldowns = {}

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

def get_user(guild_id, user_id):
    gid = str(guild_id)
    uid = str(user_id)

    if gid not in data:
        data[gid] = {}

    if uid not in data[gid]:
        data[gid][uid] = {"xp":0,"level":1,"coins":0}

    return data[gid][uid]

def xp_needed(level):
    return 150 + (level * 75)

def make_bar(current, needed, size=10):
    filled = int((current / needed) * size)
    return HEART * filled + "▫️" * (size - filled)

# ================= EVENTS =================
@bot.event
async def on_ready():
    await tree.sync()
    print("Level bot online")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    gid = message.guild.id
    uid = message.author.id
    now = time.time()

    if uid in cooldowns and now - cooldowns[uid] < XP_COOLDOWN:
        return

    cooldowns[uid] = now
    user = get_user(gid, uid)

    gained = 50 if message.channel.name == REVIEW_CHANNEL_NAME else random.randint(5,15)
    user["xp"] += gained

    needed = xp_needed(user["level"])

    if user["xp"] >= needed:
        user["xp"] -= needed
        user["level"] += 1
        reward = user["level"] * 10
        user["coins"] += reward

        await message.channel.send(
            f"🎉 {message.author.mention} leveled up to **Level {user['level']}**!\n"
            f"💰 Earned **{reward}** coins"
        )

    save_data()

@bot.event
async def on_member_remove(member):
    gid = str(member.guild.id)
    uid = str(member.id)
    if gid in data and uid in data[gid]:
        del data[gid][uid]
        save_data()

# ================= LEVEL EMBED =================
@tree.command(name="level")
async def level(interaction: discord.Interaction):
    user = get_user(interaction.guild.id, interaction.user.id)
    needed = xp_needed(user["level"])
    bar = make_bar(user["xp"], needed)

    embed = discord.Embed(color=0xF6D2A3)
    embed.set_author(name="Whiskette Levels", icon_url=interaction.user.avatar.url)
    embed.add_field(name="User", value=interaction.user.mention, inline=False)
    embed.add_field(name="Level", value=f"**{user['level']}**", inline=True)
    embed.add_field(name="Coins", value=f"**{user['coins']}** 💰", inline=True)
    embed.add_field(name="Progress", value=f"{bar}\n{user['xp']}/{needed} XP", inline=False)
    embed.set_footer(text="Keep chatting & reviewing to level up ♡")

    await interaction.response.send_message(embed=embed)

# ================= PROFILE RECEIPT =================
@tree.command(name="profile")
async def profile(interaction: discord.Interaction):
    user = get_user(interaction.guild.id, interaction.user.id)
    needed = xp_needed(user["level"])
    bar = make_bar(user["xp"], needed)

    text = f"""
⠀⠀ ⠀﹒﹒﹒⠀💌   ⠀ ***printing the receipt ***⠀ৎ
⠀⠀ ⠀                     *level order!*

_ _  user ﹒ {interaction.user.mention}
_ _  level ﹒ {user['level']}
_ _  coins ﹒ {user['coins']} 💰

{bar}
{user['xp']}/{needed} XP

> 🌷 keep chatting & reviewing to level up!
"""
    await interaction.response.send_message(text)

# ================= LEADERBOARD =================
@tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    guild_data = data.get(str(interaction.guild.id), {})
    sorted_users = sorted(guild_data.items(), key=lambda x: x[1]["level"], reverse=True)

    embed = discord.Embed(color=0xA7B3A6)
    embed.title = "🏆 Level Leaderboard"

    for i, (uid, udata) in enumerate(sorted_users[:10], start=1):
        member = interaction.guild.get_member(int(uid))
        if member:
            embed.add_field(
                name=f"{i}. {member.display_name}",
                value=f"Level {udata['level']}",
                inline=False
            )

    await interaction.response.send_message(embed=embed)

# ================= RUN =================
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not found!")

bot.run(TOKEN)