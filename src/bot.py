from dataclasses import dataclass
import discord
from discord.ext import commands
import sqlite3 as sql
import time
from utils import *
from constants import *
import random
import json
import re
import threading
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone


load_dotenv()
token = os.getenv("bot-token")
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
last_ping = 0

bot = commands.Bot(command_prefix='>', intents=intents)
db = BotDatabase.instance()

# Set up the extensions (cogs folder)
@bot.event
async def setup_hook():
    await bot.load_extension("cogs.gamble")
    await bot.load_extension("cogs.birthdays")

# Class for the info command suggest form
class InfoSuggestModal(discord.ui.Modal, title="Suggestion Form"):
    command = discord.ui.TextInput(
        label="Command",
        placeholder="Enter the command to type in eg. roma",
        max_length=50
    )
    output = discord.ui.TextInput(
        label="Output",
        placeholder="Enter the output of that command",
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        with open("src/info_suggestions.txt", "a") as f:
            f.write(f"{self.command.value} | {self.output.value}\n")
            await interaction.response.send_message("Suggestion sent!", ephemeral=True)

# Opens the info command suggest form
class OpenSuggest(discord.ui.View):
    @discord.ui.button(label="Open Form", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InfoSuggestModal())

@bot.command()
async def suggest(ctx):
    await ctx.channel.send("Click to suggest an info command", view=OpenSuggest())

@bot.command()
async def info(ctx, *, topic):
    if topic == "help":
        message = "Available info commands: "
        for info in get_json("general_info.json")["info_command"].keys():
            message += f"`{info}`, "

        message = await ctx.channel.send(message[:-2], suppress=True)
        return

    try:
        response = get_json("general_info.json")["info_command"][topic]

        if not isinstance(response, str):
            response = response[random.randint(0, len(response)-1)]
    except:
        response = f"Found no info on {topic}. All info commands can be found with `>info help`\nYou can also suggest a new one using `>suggest`"

    await ctx.channel.send(response)

@bot.command()
async def chatrevive(ctx):
    if ctx.channel.id == ANNOUNCEMENTS_CHANNEL_ID:
        return
    global last_ping

    if (last_ping + CHAT_REVIVE_TIMEOUT < time.time()):
        role = ctx.guild.get_role(1529912646248435803)
        await ctx.channel.send(f"{role.mention}")
        last_ping = time.time()
    else:
        await ctx.channel.send(f"Cannot ping chat revive for another {int(-(time.time() - (last_ping + CHAT_REVIVE_TIMEOUT))/60)} minutes")

@bot.command(name=":3")
async def colon_three(ctx):
    await ctx.channel.send(":3")

@bot.command()
async def files(ctx):
    await ctx.send("You can find most files, such as instrumentals, .svp, vocals, etc. [here](https://drive.google.com/drive/folders/1w8VHY8J7a_llbiE6TzgtPXetDUyfEBYw?usp=drive_link)." + 
                   " If something is missing please ask Roma to add it.",)

@bot.listen()
async def on_message(message):
    # If user is mod dont react to the message in hall of fame submissions
    if user_has_role(message.author, MOD_ROLE_ID):
        if message.content.startswith("!NR"):
            return

    if message.channel.id == HOF_SUBMISSION_CHANNEL_ID:
        if len(message.attachments) == 0:
            if not user_has_role(message.author, MOD_ROLE_ID):
                await message.delete()
                return

    if message.channel.id == HOF_SUBMISSION_CHANNEL_ID:
        await message.add_reaction("\u2b50")

# Logic for hall of fame submissions reaction count and sending to hof
@bot.listen()
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    if payload.channel_id != HOF_SUBMISSION_CHANNEL_ID:
        return
    if str(payload.emoji) != "\u2b50":
        return
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    reaction = discord.utils.get(message.reactions, emoji="\u2b50")
    if reaction and reaction.count <= HOF_SUBMISSION_REACTIONS:
        return
    if db.hof_message_exists(reaction.message.id):
        return

    message = reaction.message

    target_channel = bot.get_channel(HOF_CHANNEL_ID)

    embed = discord.Embed(
        description=message.content,
        color = discord.Color.gold()
    )
    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.add_field(name="Source", value=f"[Jump to Message]({message.jump_url})")
    
    embeds = [embed]

    embed.set_image(url=message.attachments[0].url)

    for attachment in message.attachments[1:]:
        img_embed = discord.Embed(color=discord.Color.gold())
        img_embed.set_image(url=attachment.url)
        embeds.appends(img_embed)

    db.add_hof_message(message.id)
    await target_channel.send(embeds=embeds)

@bot.event
async def on_member_join(member):
    roles = await member.guild.fetch_roles()
    role = discord.utils.get(roles, id=FAN_ROLE_ID)
    if role is not None:
        await member.add_roles(role, reason="Auto-role on join")

@bot.listen
async def on_message_edit(before, after):
    keywords = ["*you're", "you're*", "*your", "your*"]
    for keyword in keywords:
        if keyword in after.content.lower():
            await after.channel.send("Don't be a bum")
            await after.delete()

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if not message.author.bot:
        keywords = ["*you're", "you're*", "*your", "your*"]
        for keyword in keywords:
            if keyword in message.content.lower():
                await message.channel.send("Don't be a bum")
                await message.delete()

    if message.channel.id == HONEYPOT_CHANNEL_ID:
        if user_has_role(message.author, MOD_ROLE_ID):
            return

        try:
            await message.guild.kick(message.author, reason="Honeypot")
            for channel in message.guild.text_channels:
                await channel.purge(
                    after=datetime.now(timezone.utc) - timedelta(minutes=2),
                    check=lambda m: m.author.id == message.author.id
                )
        except discord.Forbidden:
            print(1)
        except discord.HTTPException:
            print(2)
        return

    date = message.created_at.timestamp()

    if message.author.id != ARCANE_USER_ID:
        return

    # Ping for level up if user has role
    match = re.match(r"^@(\S+) has reached level \*\*(\d+)\*\*\. GG!$", message.content)
    if match:
        username, level = match.groups()

        member = discord.utils.get(message.guild.members, name=username)
        if member:
            if not user_has_role(member, LEVELUPPING_ROLE_ID):
                await message.channel.send(f"{member.display_name} has reached level **{level}**. GG!")
                await message.delete()
                return

            await message.channel.send(f"{member.mention} has reached level **{level}**. GG!")
            await message.delete()

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(action=discord.AudiLlogAction.ban, limit=1):
        reason = entry.reason
        await user.send(f"You were banned from ROMA GANG for: {reason}")

# Error commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("I-Im not gonna answer that *b-baka*!")
        await ctx.send("https://klipy.com/gifs/anime-tsundere-6")
    else:
        log(error)

async def log(error):
    import traceback
    tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    log_message = f"```py\n{tb_text}\n```"

    if len(log_message) > 2000:
         log_message = log_message[:1990] + "\n...```"

    channel = await bot.fetch_channel(BOT_LOG_CHANNEL)
    message = await channel.send(log_message)
    await channel.send(f"An error occurred > {message.jump_url} <@852911970118271016>")


bot.run(token)
