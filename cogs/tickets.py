import discord
from discord.ext import commands


class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """Setup the ticket system"""
        embed = discord.Embed(
            title="Support Tickets",
            description="React with 🎫 to open a new support ticket!"
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction('🎫')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        if str(reaction.emoji) == '🎫':
            guild = reaction.message.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True)
            }
            channel = await guild.create_text_channel(f'ticket-{user.name}', overwrites=overwrites)
            await channel.send(f"{user.mention} Welcome to your support ticket! Please describe your issue and a staff member will be with you shortly.")

    @commands.command()
    async def close(self, ctx):
        """Close a support ticket"""
        if ctx.channel.name.startswith('ticket-'):
            try:
                # Optional: Send a confirmation message before deleting the channel
                await ctx.send("Closing this ticket...")
                await ctx.channel.delete()
            except discord.Forbidden:
                await ctx.send("I do not have permission to delete this channel.")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {e}")
        else:
            await ctx.send("This command can only be used in a ticket channel.")

# Remember to add this cog in your main.py file:
# bot.add_cog(TicketsCog(bot))
