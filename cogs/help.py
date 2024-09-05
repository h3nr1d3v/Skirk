import discord
from discord.ext import commands
import asyncio


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.color = discord.Color.blue()
        self.verify_checks = True

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Bot Commands",
            description="Here's a list of available commands. Use `!help <command>` for more info on a command.",
            color=self.color
        )

        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [
                self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(
                    command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=self.get_command_signature(command), color=self.color)
        embed.add_field(name="Description",
                        value=command.help or "No description available.")

        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(
                command.aliases), inline=False)

        if command.usage:
            embed.add_field(name="Usage", value=command.usage, inline=False)

        if command.cooldown:
            embed.add_field(
                name="Cooldown", value=f"{command.cooldown.rate} uses every {command.cooldown.per} seconds", inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=self.get_command_signature(group), color=self.color)
        embed.add_field(name="Description",
                        value=group.help or "No description available.")

        filtered = await self.filter_commands(group.commands, sort=True)
        command_signatures = [self.get_command_signature(c) for c in filtered]

        if command_signatures:
            embed.add_field(name="Subcommands", value="\n".join(
                command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"{cog.qualified_name} Commands",
            description=cog.description or "No description available.",
            color=self.color
        )

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        command_signatures = [self.get_command_signature(c) for c in filtered]
        if command_signatures:
            embed.add_field(name="Commands", value="\n".join(
                command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def command_not_found(self, string):
        return f"No command called '{string}' found."

    async def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return f"Command '{command.qualified_name}' has no subcommand named '{string}'."
        return f"Command '{command.qualified_name}' has no subcommands."

    async def send_error_message(self, error):
        embed = discord.Embed(
            title="Error", description=error, color=discord.Color.red())
        channel = self.get_destination()
        await channel.send(embed=embed)

    def get_command_signature(self, command):
        return f'{self.context.clean_prefix}{command.qualified_name} {command.signature}'

    async def command_callback(self, ctx, *, command=None):
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        # Check if it's a cog
        cog = bot.get_cog(command.title())
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # Command/Group
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        if isinstance(cmd, commands.Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
