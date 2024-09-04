import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = 1106651132375334975

LEFT_CHANNEL_ID = 1106651165879455815

BANNED_CHANNEL_ID = 1106651213438656554

UNBANNED_CHANNEL_ID = 1280941928225046641

WARNINGS_CHANNEL_ID = 1280925179186384977


class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if channel is not None:
            try:
                embed = discord.Embed(
                    title=f"Welcome to the server, {member.display_name}!",
                    description=f"We're glad to have you here, {member.mention}. To get started with our bot, try the following:",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="View All Commands",
                    value="Type `!help` to see a list of all available commands.",
                    inline=False
                )
                embed.add_field(
                    name="Get Help on a Specific Command",
                    value="Type `!help <command_name>` to get detailed information about a specific command.",
                    inline=False
                )
                await channel.send(embed=embed)
                print(
                    f"Sent welcome message to {member.name} in {channel.name}")
            except discord.Forbidden:
                print(
                    f"Failed to send welcome message to {member.name} - insufficient permissions.")
            except discord.HTTPException as e:
                print(
                    f"Failed to send welcome message to {member.name} - HTTPException: {e}")
        else:
            print(
                f"Channel with ID '{WELCOME_CHANNEL_ID}' not found in {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(LEFT_CHANNEL_ID)

        if channel is not None:
            try:
                embed = discord.Embed(
                    title=f"{member.name} has left the server.",
                    description="We hope to see you again!",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                print(
                    f"Sent departure message for {member.name} in {channel.name}")
            except discord.Forbidden:
                print(
                    f"Failed to send departure message for {member.name} - insufficient permissions.")
            except discord.HTTPException as e:
                print(
                    f"Failed to send departure message for {member.name} - HTTPException: {e}")
        else:
            print(
                f"Channel with ID '{LEFT_CHANNEL_ID}' not found in {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        channel = self.bot.get_channel(BANNED_CHANNEL_ID)

        if channel is not None:
            try:
                embed = discord.Embed(
                    title=f"{user.name} has been banned from the server.",
                    description="Please ensure to follow the server rules.",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                print(f"Sent ban message for {user.name} in {channel.name}")
            except discord.Forbidden:
                print(
                    f"Failed to send ban message for {user.name} - insufficient permissions.")
            except discord.HTTPException as e:
                print(
                    f"Failed to send ban message for {user.name} - HTTPException: {e}")
        else:
            print(
                f"Channel with ID '{BANNED_CHANNEL_ID}' not found in {guild.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        channel = self.bot.get_channel(UNBANNED_CHANNEL_ID)

        if channel is not None:
            try:
                embed = discord.Embed(
                    title=f"{user.name} has been unbanned from the server.",
                    description="Welcome back!",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
                print(f"Sent unban message for {user.name} in {channel.name}")
            except discord.Forbidden:
                print(
                    f"Failed to send unban message for {user.name} - insufficient permissions.")
            except discord.HTTPException as e:
                print(
                    f"Failed to send unban message for {user.name} - HTTPException: {e}")
        else:
            print(
                f"Channel with ID '{UNBANNED_CHANNEL_ID}' not found in {guild.name}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before != after:
            # Aquí se asume que manejas advertencias de alguna manera
            if hasattr(after, 'warnings') and after.warnings:
                channel = self.bot.get_channel(WARNINGS_CHANNEL_ID)

                if channel is not None:
                    try:
                        embed = discord.Embed(
                            title=f"Warning issued to {after.name}",
                            # Adapta esto según cómo manejes las advertencias
                            description=f"Reason: {after.warnings[-1]}",
                            color=discord.Color.orange()
                        )
                        await channel.send(embed=embed)
                        print(
                            f"Sent warning message for {after.name} in {channel.name}")
                    except discord.Forbidden:
                        print(
                            f"Failed to send warning message for {after.name} - insufficient permissions.")
                    except discord.HTTPException as e:
                        print(
                            f"Failed to send warning message for {after.name} - HTTPException: {e}")
                else:
                    print(
                        f"Channel with ID '{WARNINGS_CHANNEL_ID}' not found in {after.guild.name}")

# Recuerda agregar este cog en tu archivo principal
# bot.add_cog(WelcomeCog(bot))
