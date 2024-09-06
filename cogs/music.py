import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random
import logging
import os
from async_timeout import timeout

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('music_bot')

ffmpeg_options = {
    'options': '-vn -af "volume=0.5"'
}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '/tmp/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False,
    'extract_flat': 'in_playlist',
    'extractor_retries': 'auto',
    'socket_timeout': 30,
    'external_downloader': 'aria2c',
    'compat_opts': ['youtube-dl'],
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            logger.info(
                f"Data extracted: {data.get('title', 'Unknown title')}")
            if 'entries' in data:
                data = data['entries'][0]
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except Exception as e:
            logger.error(f"Error in from_url: {e}", exc_info=True)
            return None


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}
        self.voice_states = {}

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                try:
                    await ctx.author.voice.channel.connect()
                except discord.ClientException:
                    await ctx.send("I couldn't connect to the voice channel. Please try again.")
                    return False
            else:
                await ctx.send("You are not connected to a voice channel.")
                return False
        return True

    async def search_youtube(self, query):
        try:
            data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            if 'entries' in data:
                return data['entries']
            return []
        except Exception as e:
            logger.error(f"Error in search_youtube: {e}", exc_info=True)
            return []

    @commands.command()
    async def play(self, ctx, *, query):
        """Searches for a song and adds it to the queue"""
        if not await self.ensure_voice(ctx):
            return

        async with ctx.typing():
            try:
                async with timeout(10):  # 10 seconds timeout for search
                    search_results = await self.search_youtube(query)
                    if not search_results:
                        return await ctx.send("No results found. Please try a different search query.")

                options = '\n'.join(
                    f"{i+1}. {result['title']}" for i, result in enumerate(search_results))
                await ctx.send(f"Please choose a song by number:\n{options}\n\nType 'cancel' to cancel the selection.")

                try:
                    msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and (m.content.isdigit() or m.content.lower() == 'cancel'), timeout=30.0)
                except asyncio.TimeoutError:
                    return await ctx.send("Song selection timed out.")

                if msg.content.lower() == 'cancel':
                    return await ctx.send("Song selection cancelled.")

                try:
                    choice = int(msg.content)
                    if choice < 1 or choice > len(search_results):
                        return await ctx.send("Invalid choice. Please try again.")
                except ValueError:
                    return await ctx.send("Invalid input. Please enter a number.")

                selected_song = search_results[choice - 1]
                player = await YTDLSource.from_url(selected_song['webpage_url'], loop=self.bot.loop, stream=True)

                if player is None:
                    return await ctx.send("Couldn't process the song. Please try again with a different query.")

                if ctx.guild.id not in self.queue:
                    self.queue[ctx.guild.id] = []
                self.queue[ctx.guild.id].append(player)

            except asyncio.TimeoutError:
                return await ctx.send("The search operation timed out. Please try again.")

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f'Added to queue: {player.title}')

    async def play_next(self, ctx):
        if not self.queue[ctx.guild.id]:
            await ctx.send("Queue is empty. Use !play to add more songs.")
            return

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await ctx.send("Not connected to a voice channel. Use !join to connect.")
            return

        player = self.queue[ctx.guild.id].pop(0)
        ctx.voice_client.play(
            player, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        self.now_playing[ctx.guild.id] = player
        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def pause(self, ctx):
        """Pauses the currently playing song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused ⏸️")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command()
    async def resume(self, ctx):
        """Resumes a currently paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed ▶️")
        else:
            await ctx.send("The audio is not paused.")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Skipped ⏭️")
            await self.play_next(ctx)
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command()
    async def queue(self, ctx):
        """Displays the current song queue"""
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            return await ctx.send("The queue is empty.")
        queue_list = "\n".join(
            f"{i+1}. {song.title}" for i, song in enumerate(self.queue[ctx.guild.id]))
        await ctx.send(f"Current queue:\n{queue_list}")

    @commands.command()
    async def leave(self, ctx):
        """Clears the queue and leaves the voice channel"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue[ctx.guild.id] = []
            self.now_playing.pop(ctx.guild.id, None)
            await ctx.send("Disconnected from voice channel and cleared the queue.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

    @commands.command()
    async def now_playing(self, ctx):
        """Displays the currently playing song"""
        if ctx.guild.id in self.now_playing and self.now_playing[ctx.guild.id]:
            player = self.now_playing[ctx.guild.id]
            await ctx.send(f"Now playing: {player.title}")
        else:
            await ctx.send("Nothing is playing right now.")


def setup(bot):
    bot.add_cog(MusicCog(bot))
