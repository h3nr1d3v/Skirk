import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime, timedelta

# Constants
WELCOME_CHANNEL_ID = 1106651132375334975
LEFT_CHANNEL_ID = 1106651165879455815
BANNED_CHANNEL_ID = 1106651213438656554
UNBANNED_CHANNEL_ID = 1280941928225046641
WARNINGS_CHANNEL_ID = 1280925179186384977


class ModerationCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager
        self.warnings = {}
        self.load_warnings()

    def load_warnings(self):
        try:
            with open('warnings.json', 'r') as f:
                self.warnings = json.load(f)
        except FileNotFoundError:
            self.warnings = {}

    def save_warnings(self):
        with open('warnings.json', 'w') as f:
            json.dump(self.warnings, f)

    async def get_mod_channel(self, guild, channel_id):
        return self.bot.get_channel(channel_id)

    async def log_action(self, channel_id, message):
        channel = await self.get_mod_channel(self.bot.guilds[0], channel_id)
        if channel:
            await channel.send(message)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server."""
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kicked.')
        await self.log_action(LEFT_CHANNEL_ID, f'{member.mention} has been kicked by {ctx.author.mention} for: {reason}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server."""
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been banned.')
        await self.log_action(BANNED_CHANNEL_ID, f'{member.mention} has been banned by {ctx.author.mention} for: {reason}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """Unban a member from the server."""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} has been unbanned.')
                await self.log_action(UNBANNED_CHANNEL_ID, f'{user.mention} has been unbanned by {ctx.author.mention}.')
                return

        await ctx.send(f'User {member} not found in ban list.')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages."""
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f'{amount} messages have been cleared.')
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    @commands.has_permissions(mute_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason=None):
        """Timeout a member for a specified duration in minutes."""
        if duration < 1:
            return await ctx.send("Duration must be at least 1 minute.")

        until = datetime.utcnow() + timedelta(minutes=duration)
        await member.timeout(until, reason=reason)
        await ctx.send(f'{member.mention} has been timed out for {duration} minutes.')
        await self.log_action(WARNINGS_CHANNEL_ID, f'{member.mention} has been timed out by {ctx.author.mention} for {duration} minutes. Reason: {reason}')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member."""
        if str(member.id) not in self.warnings:
            self.warnings[str(member.id)] = []
        self.warnings[str(member.id)].append(
            {"reason": reason, "timestamp": datetime.utcnow().isoformat()})
        self.save_warnings()

        await ctx.send(f'{member.mention} has been warned for: {reason}')
        await self.log_action(WARNINGS_CHANNEL_ID, f'{member.mention} has been warned by {ctx.author.mention} for: {reason}')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """View warnings of a member."""
        user_warnings = self.warnings.get(str(member.id), [])
        if user_warnings:
            embed = discord.Embed(
                title=f"Warnings for {member}", color=discord.Color.orange())
            for i, warning in enumerate(user_warnings, 1):
                embed.add_field(
                    name=f"Warning {i}", value=f"Reason: {warning['reason']}\nDate: {warning['timestamp']}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'{member.mention} has no warnings.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock the channel, preventing new messages."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f'{channel.mention} has been locked.')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock the channel, allowing new messages."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f'{channel.mention} has been unlocked.')

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """Mute a member."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)

        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f'{member.mention} has been muted.')
        await self.log_action(WARNINGS_CHANNEL_ID, f'{member.mention} has been muted by {ctx.author.mention}. Reason: {reason}')

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f'{member.mention} has been unmuted.')
            await self.log_action(WARNINGS_CHANNEL_ID, f'{member.mention} has been unmuted by {ctx.author.mention}.')
        else:
            await ctx.send(f'{member.mention} is not muted.')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Welcome new members."""
        welcome_channel = await self.get_mod_channel(member.guild, WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(f'Welcome to the server, {member.mention}!')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log when members leave."""
        left_channel = await self.get_mod_channel(member.guild, LEFT_CHANNEL_ID)
        if left_channel:
            await left_channel.send(f'{member.mention} has left the server.')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument passed. Please check the command usage.")
        else:
            await ctx.send(f"An error occurred: {error}")


def setup(bot):
    bot.add_cog(ModerationCog(bot, None))
