import discord
from discord.ext import commands


class AdminCog(commands.Cog):
    def __init__(self, bot, config_manager):
        self.bot = bot
        self.config_manager = config_manager

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, new_prefix: str):
        """Set a new command prefix for the bot."""
        self.bot.command_prefix = new_prefix
        self.config_manager.update_config('prefix', new_prefix)
        await ctx.send(f'Command prefix updated to: {new_prefix}')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_feature(self, ctx, feature: str):
        """Toggle a bot feature on or off."""
        current_state = self.config_manager.get_config(feature, False)
        new_state = not current_state
        self.config_manager.update_config(feature, new_state)
        await ctx.send(f'Feature "{feature}" is now {"enabled" if new_state else "disabled"}.')
