from datetime import datetime, timezone

from discord.ext import commands

from constants import *
from utils import *

db = BotDatabase.instance()


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def istodaymikusbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if is_today(now, 8, 31): # now.month == 8 and now.day == 31:
            message = "yes"
        if is_today(now, 3, 9): # now.month == 3 and now.day == 9:
            message = "no, but its miku day"

        await ctx.channel.send(message)

    @commands.command()
    async def istodaygumisbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if is_today(now, 6, 26): # now.month == 6 and now.day == 26:
            message = "yes"

        await ctx.channel.send(message)

    @commands.command()
    async def istodaytetosbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if is_today(now, 4, 1): # now.month == 4 and now.day == 1:
            message = "yes"

        await ctx.channel.send(message)

    @commands.command()
    async def istodayyixisbirthday(self, ctx):
        message = "no"
        now = datetime.now(timezone.utc)
        if is_today(now, 3, 15): # now.month == 3 and now.day == 15:
            message = "yes"

        await ctx.channel.send(message)

async def setup(bot):
    await bot.add_cog(Birthdays(bot))


def is_today(now: datetime, target_month: int, target_day: int) -> bool: # helper func to dedupe and simplify adding new birthdays (I know it's a tiny thing but hey)
    return now.month == target_month and now.day == target_day
