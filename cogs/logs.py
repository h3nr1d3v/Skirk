import discord
from discord.ext import commands
import datetime

LOG_CHANNEL_ID = 1280954927065202742


class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Replace with your log channel ID
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title="Message Deleted", description=f"In {message.channel.mention}", color=discord.Color.red())
        embed.add_field(name="Content", value=message.content)
        embed.set_author(name=message.author.name,
                         icon_url=message.author.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Replace with your log channel ID
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title="Member Joined", description=f"{member.mention} joined the server", color=discord.Color.green())
        embed.set_author(name=member.name, icon_url=member.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Replace with your log channel ID
        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title="Member Left", description=f"{member.mention} left the server", color=discord.Color.orange())
        embed.set_author(name=member.name, icon_url=member.avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        await channel.send(embed=embed)

# Remember to add this cog in your main.py file:
# bot.add_cog(LogsCog(bot))
