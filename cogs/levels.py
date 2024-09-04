import discord
from discord.ext import commands
import json


class LevelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = self.load_levels()

    def load_levels(self):
        try:
            with open('levels.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_levels(self):
        with open('levels.json', 'w') as f:
            json.dump(self.levels, f)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        author_id = str(message.author.id)
        if author_id not in self.levels:
            self.levels[author_id] = {"xp": 0, "level": 1}

        self.levels[author_id]["xp"] += 1
        xp = self.levels[author_id]["xp"]
        lvl = self.levels[author_id]["level"]

        if xp >= lvl * 100:
            self.levels[author_id]["level"] += 1
            await message.channel.send(f'{message.author.mention} has reached level {lvl+1}!')

        self.save_levels()

    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        """Check your or someone else's level"""
        member = member or ctx.author
        member_id = str(member.id)

        if member_id not in self.levels:
            await ctx.send("This user hasn't earned any XP yet.")
            return

        xp = self.levels[member_id]["xp"]
        lvl = self.levels[member_id]["level"]

        await ctx.send(f'{member.mention} is level {lvl} with {xp} XP.')

# Remember to add this cog in your main.py file:
# bot.add_cog(LevelsCog(bot))
