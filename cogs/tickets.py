import discord
from discord.ext import commands

TicketsChannel = 1281013321679634557


class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx, *, category_name="Tickets"):
        """Setup the ticket system with optional category"""
        category = discord.utils.get(ctx.guild.categories, name=category_name)
        if not category:
            category = await ctx.guild.create_category(category_name)

        embed = discord.Embed(
            title="Support Tickets",
            description="React with 🎫 to open a new support ticket!"
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction('🎫')

        # Store the message ID and category ID in a database or file if needed
        # Example: store in a file (for demonstration purposes)
        with open('ticket_setup.txt', 'w') as f:
            f.write(f"{message.id}\n{category.id}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        # Read the setup information
        try:
            with open('ticket_setup.txt', 'r') as f:
                setup_message_id = int(f.readline().strip())
                category_id = int(f.readline().strip())
        except FileNotFoundError:
            return

        if reaction.message.id == setup_message_id and str(reaction.emoji) == '🎫':
            guild = reaction.message.guild
            category = discord.utils.get(guild.categories, id=category_id)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True)
            }
            channel = await guild.create_text_channel(f'ticket-{user.name}', category=category, overwrites=overwrites)
            await channel.send(f"{user.mention} Welcome to your support ticket! Please describe your issue and a staff member will be with you shortly.")
            log_channel = discord.utils.get(
                guild.text_channels, name="ticket-logs")
            if log_channel:
                await log_channel.send(f"Ticket created: {channel.mention} by {user.mention}")

    @commands.command()
    async def close(self, ctx):
        """Close a support ticket"""
        if ctx.channel.name.startswith('ticket-'):
            try:
                # Send a confirmation message before deleting the channel
                await ctx.send("Closing this ticket...")
                await ctx.author.send("Your support ticket has been closed.")
                log_channel = discord.utils.get(
                    ctx.guild.text_channels, name="ticket-logs")
                if log_channel:
                    await log_channel.send(f"Ticket closed: {ctx.channel.mention}")
                await ctx.channel.delete()
            except discord.Forbidden:
                await ctx.send("I do not have permission to delete this channel.")
            except discord.HTTPException as e:
                await ctx.send(f"An error occurred: {e}")
        else:
            await ctx.send("This command can only be used in a ticket channel.")

    @commands.command()
    async def reopen(self, ctx):
        """Reopen a closed support ticket"""
        if ctx.channel.name.startswith('ticket-'):
            category = discord.utils.get(ctx.guild.categories, name="Tickets")
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True)
            }
            new_channel = await ctx.guild.create_text_channel(f'ticket-{ctx.author.name}', category=category, overwrites=overwrites)
            await new_channel.send(f"{ctx.author.mention} Your ticket has been reopened. Please describe your issue and a staff member will be with you shortly.")
            await ctx.send("Your ticket has been reopened.")
        else:
            await ctx.send("This command can only be used in a ticket channel.")

    @commands.command()
    async def help_tickets(self, ctx):
        """Show help information about the ticket system"""
        help_embed = discord.Embed(
            title="Ticket System Help",
            description="Here are the commands you can use:",
            color=discord.Color.blue()
        )
        help_embed.add_field(name="!setup_tickets",
                             value="Set up the ticket system.", inline=False)
        help_embed.add_field(
            name="!close", value="Close the current support ticket.", inline=False)
        help_embed.add_field(
            name="!reopen", value="Reopen a closed support ticket.", inline=False)
        await ctx.send(embed=help_embed)

# Add this cog in your main.py file
# bot.add_cog(TicketsCog(bot))
