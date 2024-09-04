import discord
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bot Commands", description="Here's a list of available commands:", color=discord.Color.blue())

        for cog, commands in mapping.items():
            if cog:
                filtered = await self.filter_commands(commands, sort=True)
                command_signatures = [
                    self.get_command_signature(c) for c in filtered]
                if command_signatures:
                    cog_name = cog.qualified_name
                    embed.add_field(name=cog_name, value="\n".join(
                        command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=self.get_command_signature(command), color=discord.Color.green())
        embed.add_field(
            name="Help", value=command.help or "No description available.")
        alias = command.aliases
        if alias:
            embed.add_field(
                name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands", description="Here's a list of commands for this category:", color=discord.Color.orange())

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        command_signatures = [self.get_command_signature(c) for c in filtered]
        if command_signatures:
            embed.add_field(name=cog.qualified_name, value="\n".join(
                command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def parse_help_args(self, args):
        if args:
            return args[0].lower()
        return None

    async def get_command_help(self, command_name):
        command = self.bot.get_command(command_name)
        if command:
            await self.send_command_help(command)
        else:
            await self.get_destination().send("No command found with that name.")

    async def send_help(self, ctx, command_name=None):
        if command_name:
            # If the command_name is provided, show help for that specific command or cog
            cog = self.bot.get_cog(command_name)
            if cog:
                await self.send_cog_help(cog)
            else:
                await self.get_command_help(command_name)
        else:
            # If no command_name is provided, show general bot help
            await self.send_bot_help(self.bot.cogs)
