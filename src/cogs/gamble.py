import discord
from discord.ext import commands
from utils import *
from constants import *
import random

db = BotDatabase.instance()

class GambleButtons(discord.ui.View):
    def __init__(self, bot, author_id, private, channel_id):
        super().__init__()
        self.author_id = author_id
        self.channel = channel_id
        self.bot = bot

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isnt your button!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Gift", style=discord.ButtonStyle.green)
    async def gift_button(self, interaction, button):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        await interaction.response.send_message("Please type the amount of money you would like to gift")
        reply = await interaction.client.wait_for("message", check=check, timeout=60.0)
        amount = 0
        try:
            amount = int(reply.content)
        except Exception:
            await reply.reply("Please restart and enter numbers only.")
            return

        data = db.get_user(interaction.user.id, interaction.guild.id)
        if data["points"] < amount:
            await reply.reply("You dont have enough money!")
            return

        await reply.reply("Please type the username (not display name) of the person you want to gift money to")
        reply = await interaction.client.wait_for("message", check=check, timeout=60.0)
        username = reply.content

        member = discord.utils.get(interaction.guild.members, name=username)
        if member == None:
            await reply.reply(f"Couldnt find '{username}'.")
            return

        db.update_points(interaction.guild.id, interaction.user.id, -amount)
        db.update_points(interaction.guild.id, member.id, amount)

        await interaction.channel.send(f"Successfully gifted {amount} money to {username}.")

    @discord.ui.button(label="Higher or Lower", style=discord.ButtonStyle.blurple)
    async def hol_button(self, interaction, button):
        embed = discord.Embed(
            title="Higher or Lower",
            description="Higher or Lower gives you a number between 0-100 (inclusive) and you have to guess whether the next number is higher or lower than the current one.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=HigherOrLower(self.bot, self.author_id, self.channel))

    #@discord.ui.button(label="Mod Tools", style=discord.ButtonStyle.red)
    async def mod_button(self, interaction, button):
        if not is_mod(interaction.user):
            await interaction.response.send_message("You are not a moderator!")
            return

        await interaction.response.send_message("Mod Tools", view=ModTools(self.bot, self.author_id, self.channel), ephemeral=True)

class HigherOrLower(discord.ui.View):
    def __init__(self, bot, author_id, channel_id):
        super().__init__()
        self.bot = bot
        self.author_id = author_id
        self.channel_id = channel_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isnt your button!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Start", style=discord.ButtonStyle.blurple)
    async def start_buttons(self, interaction, button):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        await interaction.response.send_message("Lets go!")
        message = await interaction.original_response()
        number = random.randint(0, 100)
        while True:
            new_number = random.randint(0, 100)
            embed = discord.Embed(
                title="Higher or Lower",
                description=number,
                color=discord.Color.blue()
            )

            message = await message.reply(embed=embed)

            message = await interaction.client.wait_for("message", check=check, timeout=60.0)

            if message.lower() == "higher" and new_number > number:
                pass
            elif message.lower() == "lower" and new_number < number:
                pass
            else:
                pass

class ModTools(discord.ui.View):
    def __init__(self, bot, author_id, channel):
        super().__init__()
        self.author_id = author_id
        self.bot = bot

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isnt your button!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Change Money", style=discord.ButtonStyle.blurple)
    async def change_money_button(self, interaction, button):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        await interaction.response.send_message("How much money to you want to give/take?")
        reply = await interaction.client.wait_for("message", check=check, timeout=60.0)
        amount = 0
        try:
            amount = int(reply.content)
        except Exception:
            await reply.reply("Please restart and enter numbers only.")
            return

        await reply.reply("Please type the username (not display name) of the person you want to give money to")
        reply = await interaction.client.wait_for("message", check=check, timeout=60.0)
        username = reply.content

        member = discord.utils.get(interaction.guild.members, name=username)
        if member == None:
            await reply.reply(f"Couldnt find '{username}'.")
            return

        db.update_points(interaction.guild.id, member.id, amount)


class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gamble(self, ctx):
        if not user_has_role(ctx.author, MOD_ROLE_ID):
            await ctx.channel.send("You do not have permission to use that command!")
            return

        data = db.get_user(ctx.author.id, ctx.guild.id)
        if data is None:
            db.add_user(ctx.author.id, ctx.guild.id)
            data = db.get_user(ctx.author.id, ctx.guild.id)

        message = f"You have {data['points']} money.\nWhat would you like to do?"
        await ctx.channel.send(message, view=GambleButtons(self.bot, ctx.author.id, False, ctx.channel.id))


async def setup(bot):
    await bot.add_cog(Gamble(bot))
