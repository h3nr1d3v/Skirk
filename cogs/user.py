import discord
from discord.ext import commands
from typing import Optional


class UserCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager

    @commands.command()
    async def info(self, ctx):
        """Get information about the server."""
        embed = discord.Embed(
            title=f"Information about {ctx.guild.name}", color=discord.Color.green())
        embed.add_field(name="Server Owner",
                        value=ctx.guild.owner.mention, inline=False)
        embed.add_field(name="Server Created At", value=discord.utils.format_dt(
            ctx.guild.created_at, style='F'), inline=False)
        embed.add_field(name="Member Count",
                        value=ctx.guild.member_count, inline=False)
        embed.add_field(name="Text Channels", value=len(
            ctx.guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(
            ctx.guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(ctx.guild.roles), inline=True)
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!", description=f"Latency: {latency}ms", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        """Get information about a user."""
        member = member or ctx.author
        roles = [role.mention for role in member.roles if role !=
                 ctx.guild.default_role]
        embed = discord.Embed(
            title=f"User Info - {member}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(
            name="Nickname", value=member.nick if member.nick else "None", inline=False)
        embed.add_field(name="Joined", value=discord.utils.format_dt(
            member.joined_at, style='F'), inline=False)
        embed.add_field(name="Created", value=discord.utils.format_dt(
            member.created_at, style='F'), inline=False)
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(
            roles) if roles else "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
