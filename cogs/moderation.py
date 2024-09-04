import discord
from discord.ext import commands
import asyncio

WELCOME_CHANNEL_ID = 1106651132375334975

LEFT_CHANNEL_ID = 1106651165879455815

BANNED_CHANNEL_ID = 1106651213438656554

UNBANNED_CHANNEL_ID = 1280941928225046641

WARNINGS_CHANNEL_ID = 1280925179186384977


class ModerationCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager
        self.warnings = {}  # Dictionary to keep track of warnings

    async def get_mod_channel(self, guild, channel_name):
        """Helper function to get a moderation channel by name."""
        category = discord.utils.get(guild.categories, name="Moderation")
        if category:
            return discord.utils.get(category.channels, name=channel_name)
        return None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server."""
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kicked.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server."""
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been banned.')

        log_channel = await self.get_mod_channel(ctx.guild, BANNED_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f'{member.mention} has been banned by {ctx.author.mention} for: {reason}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member: str):
        """Unban a member from the server by their username#discriminator or ID."""
        user = None
        try:
            # Try to parse the argument as an ID
            user_id = int(member)
            user = discord.Object(id=user_id)
        except ValueError:
            # The argument is not an ID, so try to parse it as username#discriminator
            parts = member.split('#')
            if len(parts) == 2:
                username, discriminator = parts
                # Find the banned user by their username and discriminator
                banned_users = await ctx.guild.bans()
                user = discord.utils.get(
                    banned_users, user__name=username, user__discriminator=discriminator)
            else:
                await ctx.send("Invalid format. Use `username#discriminator` or user ID.")
                return

        if user:
            try:
                await ctx.guild.unban(user)
                await ctx.send(f'{user} has been unbanned.')

                log_channel = await self.get_mod_channel(ctx.guild, UNBANNED_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f'{user} has been unbanned by {ctx.author.mention}.')
            except discord.NotFound:
                await ctx.send('User not found in the banned list.')
            except discord.Forbidden:
                await ctx.send('I do not have permission to unban this user.')
        else:
            await ctx.send('User not found or invalid format.')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages."""
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'{amount} messages have been cleared.', delete_after=5)

    @commands.command()
    @commands.has_permissions(mute_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason=None):
        """Mute a member for a specified duration in minutes."""
        if duration < 1:
            await ctx.send("Duration must be at least 1 minute.")
            return

        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True)

        await member.add_roles(role, reason=reason)
        await ctx.send(f'{member.mention} has been muted for {duration} minutes.')

        await asyncio.sleep(duration * 60)
        await member.remove_roles(role, reason="Timeout expired")
        await ctx.send(f'{member.mention} has been unmuted.')

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member with a message."""
        if member.id not in self.warnings:
            self.warnings[member.id] = []
        self.warnings[member.id].append(reason)

        # Send a notification in the warnings channel
        warn_channel = await self.get_mod_channel(ctx.guild, WARNINGS_CHANNEL_ID)
        if warn_channel:
            await warn_channel.send(f'{member.mention} has been warned by {ctx.author.mention} for: {reason}')

        await ctx.send(f'{member.mention} has been warned for: {reason}')

    @commands.command()
    async def warnings(self, ctx, member: discord.Member):
        """View warnings of a member."""
        user_warnings = self.warnings.get(member.id, [])
        if user_warnings:
            await ctx.send(f'Warnings for {member.mention}:\n' + '\n'.join(user_warnings))
        else:
            await ctx.send(f'{member.mention} has no warnings.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Lock the channel, preventing new messages."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f'This channel has been locked.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlock the channel, allowing new messages."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f'This channel has been unlocked.')

    # Handle missing permissions gracefully
    @kick.error
    @ban.error
    @unban.error
    @clear.error
    @timeout.error
    @warn.error
    @warnings.error
    @lock.error
    @unlock.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument passed. Please check the command usage.")
        else:
            await ctx.send(f"An error occurred: {error}")

# Setup function to add the cog to the bot


def setup(bot):
    bot.add_cog(ModerationCog(bot, None))
