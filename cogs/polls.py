import discord
from discord.ext import commands


class PollsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poll(self, ctx, question, *options):
        """Create a poll"""
        if len(options) > 10:
            await ctx.send("You can only have up to 10 options.")
            return

        if len(options) < 2:
            await ctx.send("You need at least 2 options.")
            return

        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                     '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)

        embed = discord.Embed(title=question, description=''.join(description))
        react_message = await ctx.send(embed=embed)

        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

    @commands.command()
    async def quickpoll(self, ctx, *, question):
        """Create a quick yes/no poll"""
        await ctx.message.delete()
        embed = discord.Embed(title="Poll", description=question)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')
