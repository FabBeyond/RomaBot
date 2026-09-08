import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from dotenv import load_dotenv

from constants import *
from utils import *

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
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        data = get_json("general_info.json")
        if self.command.value in data["info_command"]:
            await interaction.response.send_message("Command already exists!", ephemeral=True)
            return

        fab = await bot.fetch_user(FAB_USER_ID)
        await fab.send(f"{interaction.user.name} suggested:\n" + \
            f"`{self.command.value}` | `{self.output.value}`")
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
    data = get_json("general_info.json")["info_command"]
    if topic == "help":
        message = "Available info commands: "
        for info_field in data:
            message += f"`{info_field}`, "
        return

    try:
        response = data[topic]

        if not isinstance(response, str):
            response = response[random.randint(0, len(response)-1)]
    except (KeyError, ValueError):
        response = f"Found no info on {topic}. All info commands can be found with `>info help`\nYou can also suggest a new one using `>suggest`"

    await ctx.channel.send(response)

@bot.command()
async def potetochips(ctx):
    await ctx.channel.send("Buy some poteto chips!\n https://www.romaloid.com/potetochips")

@bot.command()
async def chatrevive(ctx):
    if ctx.channel.id == ANNOUNCEMENTS_CHANNEL_ID:
        return
    global last_ping

    if (last_ping + CHAT_REVIVE_TIMEOUT < time.time()):
        role = ctx.guild.get_role(1529912646248435803) # FIX: magic variable
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

# Logic for hall of fame submissions reaction count and sending to hof
@bot.listen()
async def on_raw_reaction_add(payload):
    if payload.guild_id is None:
        channel = await bot.fetch_channel(payload.channel_id)
        if isinstance(channel, discord.DMChannel) and channel.recipient and channel.recipient.id == FAB_USER_ID:
            message = await channel.fetch_message(payload.message_id)
            com, out = message.content.replace("`", "").split("\n")[1].split(" | ")
            data = get_json("general_info.json")
            data["info_command"][com] = out
            write_json("general_info.json", data)

    if bot.user is not None and payload.user_id == bot.user.id:
        return
    if payload.channel_id != HOF_SUBMISSION_CHANNEL_ID:
        return
    if str(payload.emoji) != "\u2b50": # Star Emoji
        return
    channel = bot.get_channel(payload.channel_id)
    if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel, discord.DMChannel, discord.GroupChannel)):
        return
    message = await channel.fetch_message(payload.message_id)
    reaction = discord.utils.get(message.reactions, emoji="\u2b50")
    if not reaction or reaction.count <= HOF_SUBMISSION_REACTIONS:
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
        embeds.append(img_embed)

    db.add_hof_message(message.id)
    if not isinstance(target_channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel, discord.DMChannel, discord.GroupChannel)):
        return
    await target_channel.send(embeds=embeds)

@bot.event
async def on_member_join(member):
    roles = await member.guild.fetch_roles()
    role = discord.utils.get(roles, id=FAN_ROLE_ID)
    if role is not None:
        await member.add_roles(role, reason="Auto-role on join")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.id == ARCANE_USER_ID:
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
        return

    if message.author.bot:
        return

    if random.randint(1, 1000) == 1:
        rand = random.randint(1, 5)
        if rand == 1:
            await message.channel.send("Want a break from the ads? Buy ROMA BOT premium!")
        elif rand == 2:
            await message.channel.send("Subscribe to ROMA on Youtube!!!! https://www.youtube.com/@ROMALOID")
        elif rand > 2:
            await message.channel.send("Buy some poteto chips!\n https://www.romaloid.com/potetochips")

    if (
        message.channel.id == HOF_SUBMISSION_CHANNEL_ID
        and len(message.attachments) == 0
    ):
          await message.delete()
          return
    if message.channel.id == HOF_SUBMISSION_CHANNEL_ID:
      await message.add_reaction("⭐")

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

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
        if entry.target.id == user.id:
            reason = entry.reason
            try:
                await user.send(f"You were banned from ROMA GANG for: {reason}")
            except discord.Forbidden:
                pass

@bot.event
async def on_member_remove(member):
    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
        if entry.target.id == member.id:
            reason = entry.reason
            try:
                await member.send(f"You were kicked from ROMA GANG for: {reason}")
            except discord.Forbidden:
                pass

# Error commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("I-Im not gonna answer that *b-baka*!")
        await ctx.send("https://klipy.com/gifs/anime-tsundere-6")
    else:
        await log(ctx, error)

async def log(ctx, error):
    import traceback
    tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    log_message = f"```py\n{tb_text}\n```"

    if len(log_message) > 2000:
         log_message = log_message[:1990] + "\n...```"

    channel = await bot.fetch_channel(BOT_LOG_CHANNEL)
    if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel, discord.StageChannel)):
        return
    message = await channel.send(log_message)
    await ctx.channel.send(f"An error occurred > {message.jump_url} <@852911970118271016>")

if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set")
bot.run(token)
