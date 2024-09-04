import discord
from discord.ext import commands


class UserCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager

    @commands.command()
    async def info(self, ctx):
        """Get information about the server."""
        embed = discord.Embed(
            title=f"Information about {ctx.guild.name}", color=0x00ff00)
        embed.add_field(name="Server Owner",
                        value=ctx.guild.owner, inline=False)
        embed.add_field(name="Server Created At", value=ctx.guild.created_at.strftime(
            "%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="Member Count",
                        value=ctx.guild.member_count, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'Pong! Latency: {latency}ms')
