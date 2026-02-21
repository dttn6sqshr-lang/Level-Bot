import discord
from discord import app_commands
import random
import json
import os

TOKEN = os.getenv("TOKEN")

DATA_FILE = "levels.json"

XP_PER_MESSAGE = 5
REVIEW_XP = 50
COOLDOWN = 60

LEVELUP_CHANNEL_NAME = "𖦹・🍄﹕bots！"
REVIEW_CHANNEL_NAME = "✿﹒⤷﹒﹒﹒reviews"

REWARD_LEVELS = {4: 50, 9: 100, 27: 300, 29: 500}

HEART = "<:CC_heart:1474162033179230352>"
CHAT = "<:CC_chatbubble:1474578856144011338>"
TROPHY = "<:CC_trophy:1474577678790299821>"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load():
    with open(DATA_FILE) as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def xp_needed(level):
    return int(150 + (level ** 2.3))

def heart_bar(xp, need):
    filled = int((xp / need) * 10)
    return HEART * filled + "🤍" * (10 - filled)

def color():
    return random.randint(0xC1E1C1, 0xFFD1DC)

users = load()
cooldowns = {}

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"xp": 0, "level": 0}
    return users[uid]

@bot.event
async def on_ready():
    await tree.sync()
    print("Level bot online")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    user = get_user(uid)

    if uid in cooldowns:
        return

    cooldowns[uid] = True
    bot.loop.call_later(COOLDOWN, cooldowns.pop, uid)

    # XP logic
    if message.channel.name == REVIEW_CHANNEL_NAME:
        user["xp"] += REVIEW_XP
    else:
        user["xp"] += XP_PER_MESSAGE

    need = xp_needed(user["level"])

    if user["xp"] >= need:
        user["xp"] -= need
        user["level"] += 1

        reward = REWARD_LEVELS.get(user["level"], 0)

        levelup_text = f"""
_ _
      ∂𝜚       {message.author.display_name}  ─
        ❤︎   Level {user['level']}   ❤︎
_ _
"""

        if reward:
            levelup_text += f"\n🎁 Reward: {reward} sugar bits"

        # send ONLY in bots channel
        levelup_channel = discord.utils.get(
            message.guild.text_channels, name=LEVELUP_CHANNEL_NAME
        )

        if levelup_channel:
            await levelup_channel.send(
                f"{message.author.mention}\n{levelup_text}"
            )

    save(users)

# PROFILE
@tree.command(name="profile")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    u = get_user(user.id)
    need = xp_needed(u["level"])

    bar = heart_bar(u["xp"], need)

    text = f"""
_ _
    e       {user.display_name}      ╮
        ıllı  --  level {u['level']}
00:00 ━⌕━━━ 00:00

{bar}
{u['xp']} / {need} XP
"""

    embed = discord.Embed(description=text, color=color())
    await interaction.response.send_message(embed=embed)

# LEADERBOARD VIEW
class LeaderboardView(discord.ui.View):
    def __init__(self, data, page=0):
        super().__init__(timeout=None)
        self.data = data
        self.page = page

    def make_embed(self):
        embed = discord.Embed(
            title=f"{TROPHY} Level Leaderboard",
            color=color()
        )

        start = self.page * 10
        end = start + 10
        sorted_users = sorted(self.data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)

        text = ""
        rank = start + 1

        for uid, stats in sorted_users[start:end]:
            member = bot.get_user(int(uid))
            if member:
                text += f"{rank}. {member.mention} — Level {stats['level']}\n"
                rank += 1

        embed.description = f"## {TROPHY} Level Leaderboard\n\n{text}"
        return embed

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

@tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    view = LeaderboardView(users)
    await interaction.response.send_message(embed=view.make_embed(), view=view)

bot.run(TOKEN)