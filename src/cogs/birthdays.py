import discord
from discord.ext import commands
from datetime import datetime, timezone
from utils import *
from constants import *

db = BotDatabase.instance()

class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def istodaymikusbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if now.month == 8 and now.day == 31:
            message = "yes"
        if now.month == 3 and now.day == 9:
            message = "no, but its miku day"

        await ctx.channel.send(message)

    @commands.command()
    async def istodaygumisbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if now.month == 6 and now.day == 26:
            message = "yes"

        await ctx.channel.send(message)

    @commands.command()
    async def istodaytetosbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if now.month == 4 and now.day == 1:
            message = "yes"

        await ctx.channel.send(message)

    @commands.command()
    async def istodayyixisbirthday(ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if now.month == 3 and now.day == 15:
            message = "yes"

        await ctx.channel.send(message)

async def setup(bot):
    await bot.add_cog(Birthdays(bot))
