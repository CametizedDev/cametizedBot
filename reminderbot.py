import discord
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import os
import string

def get_token():
    token_path = os.path.join(os.path.dirname(__file__), "token.txt")
    if os.path.isfile(token_path):
        with open(token_path, "r") as f:
            return f.read().strip()

TOKEN = get_token()

CAM = 1154180718121992334
ADMINS = [1082533157867356244, 319529334341632000, 536264328655929369, 511313788641738763]
ALLOWED_USER_IDS = set([CAM] + ADMINS)
DEFAULT_TARGET_ID = 0
DEFAULT_REMINDER_MESSAGE = "hiii naoomiiiiii, can u work on like literally anything pleasseee :D:D:D -cam"
STATUS_MESSAGE = "alright, what's poppingggg...?"

BLACKLIST = {0} 

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
scheduler = AsyncIOScheduler()
recent_dm_senders = {}
recently_forwarded = set()

@bot.event
async def on_ready():
    print(f'logged as {bot.user}')
    await bot.change_presence(activity=discord.Game(name=STATUS_MESSAGE))
    await tree.sync()
    if not scheduler.running:
        scheduler.add_job(scheduled_reminder, 'interval', minutes=15)
        scheduler.start()

async def scheduled_reminder():
    try:
        user = await bot.fetch_user(DEFAULT_TARGET_ID)
        await user.send(DEFAULT_REMINDER_MESSAGE)
        print(f"reminder sent to: {user.name}")
    except discord.Forbidden:
        print("reminder failed: check errors")

def format_attachments(message: discord.Message):
    parts = []
    if message.attachments:
        parts += [f"File: {a.url}" for a in message.attachments]
    if message.stickers:
        parts += [f"Sticker: {s.name} (ID: {s.id})" for s in message.stickers]
    for word in message.content.split():
        if word.startswith("<:") or word.startswith("<a:"):
            parts.append(f"Emoji: {word}")
    return "\n".join(parts)

def clean_text(text):
    return ''.join(filter(lambda x: x in string.printable, text))

@tree.command(name="message", description="msg sm1")
@app_commands.describe(member="who?", message="txty")
async def remind(interaction: discord.Interaction, member: discord.Member, message: str):
    if interaction.user.id not in ALLOWED_USER_IDS:
        await interaction.response.send_message("yo u cant do that br", ephemeral=True)
        return
    try:
        await member.send(message)
        await interaction.response.send_message("sent", ephemeral=True)
    except discord.Forbidden:
        if interaction.response.is_done():
            await interaction.followup.send("didn't send", ephemeral=True)
        else:
            await interaction.response.send_message("didn't send", ephemeral=True)

@tree.command(name="reply", description="rply to last msg")
@app_commands.describe(message="txty", attachment="file?")
async def reply(interaction: discord.Interaction, message: str, attachment: discord.Attachment = None):
    if interaction.user.id not in ALLOWED_USER_IDS:
        return await interaction.response.send_message("nono u no do", ephemeral=True)
    uid = recent_dm_senders.get(interaction.user.id)
    if not uid:
        return await interaction.response.send_message("no one has sent smth", ephemeral=True)
    user = await bot.fetch_user(uid)
    try:
        if attachment:
            file = await attachment.to_file()
            await user.send(content=message, file=file)
        else:
            await user.send(message)
        await interaction.response.send_message("senty", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("failedy", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    print(f"on_message triggered by: {message.author} | {message.content}")
    if message.author.bot or message.author.id == bot.user.id:
        return

    if isinstance(message.channel, discord.DMChannel):
        if message.author.id == bot.user.id or message.author.bot:
            return
        if CAM == bot.user.id:
            print("CAM is the bot itself! Not forwarding.")
            return
        msg_key = (message.author.id, message.content, tuple(a.url for a in message.attachments))
        if msg_key in recently_forwarded:
            print("Already forwarded this DM, skipping.")
            return
        recently_forwarded.add(msg_key)
        if message.author.id in BLACKLIST:
            try:
                await message.channel.send("your on the cambot blacklist, if you think this is an issue, please dm Cam | @Cametized")
                print(f"[BLACKLIST] msg from {message.author} | blocked")
            except discord.Forbidden:
                print(f"[BLACKLIST] cant reply to {message.author}")
            return
        admin = await bot.fetch_user(CAM)
        try:
            content = (
                f"**DM from {message.author}:**\n{message.content}\n"
            )
            extra = format_attachments(message)
            if extra:
                content += f"\n{extra}"
            await admin.send(content)
            recent_dm_senders[message.author.id] = message.author.id
            print(f"[DM] Sent to CAM: {content}")
        except discord.Forbidden:
            print("didn't forward, check error")
        return

    if not isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)