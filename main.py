import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import asyncio
from cogs.admin import AdminCog
from cogs.user import UserCog
from cogs.moderation import ModerationCog
from utils.error_handler import ErrorHandler
from utils.config_manager import ConfigManager
from cogs.music import MusicCog
from cogs.chatgpt import ChatGPTCog
from cogs.levels import LevelsCog
from cogs.polls import PollsCog
from cogs.reminders import RemindersCog
from cogs.games import GamesCog
from cogs.tickets import TicketsCog
from cogs.logs import LogsCog
from cogs.translation import TranslationCog
from cogs.help import HelpCog
from cogs.welcome import WelcomeCog
from cogs.anime import AnimeCog
# Import the function to start the webserver
from webserver import start_webserver

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load configuration
config_manager = ConfigManager('config.json')


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="🌸 ꜱᴋɪʀᴋ ┊!ʜᴇʟᴘ"))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    # Add custom message handling logic here
    if 'hello' in message.content.lower():
        await message.channel.send('Hello there!')


async def main():
    # Start the web server
    start_webserver()

    # Load cogs
    await bot.add_cog(AdminCog(bot, config_manager))
    await bot.add_cog(UserCog(bot, config_manager))
    await bot.add_cog(ModerationCog(bot, config_manager))
    await bot.add_cog(MusicCog(bot))
    await bot.add_cog(ChatGPTCog(bot))
    await bot.add_cog(LevelsCog(bot))
    await bot.add_cog(PollsCog(bot))
    await bot.add_cog(RemindersCog(bot))
    await bot.add_cog(GamesCog(bot))
    await bot.add_cog(TicketsCog(bot))
    await bot.add_cog(LogsCog(bot))
    await bot.add_cog(TranslationCog(bot))
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(WelcomeCog(bot))
    await bot.add_cog(AnimeCog(bot))

    # Set up error handling
    await bot.add_cog(ErrorHandler(bot))

    # Run the bot
    await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
