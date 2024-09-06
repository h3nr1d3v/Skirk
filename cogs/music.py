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
            await asyncio.sleep(random.uniform(1, 3))
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

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""
        if not await self.ensure_voice(ctx):
            return
        await ctx.send("Joined the voice channel.")

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a song"""
        if not await self.ensure_voice(ctx):
            return

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                if player is None:
                    return await ctx.send("Couldn't find the song. Please try again with a different query.")
            except Exception as e:
                logger.error(f"Error in play command: {e}", exc_info=True)
                return await ctx.send(f"An error occurred: {str(e)}")

            if ctx.guild.id not in self.queue:
                self.queue[ctx.guild.id] = []
            self.queue[ctx.guild.id].append(player)

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
            [f"{i+1}. {song.title}" for i, song in enumerate(self.queue[ctx.guild.id])])
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

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user and after.channel is None:
            guild = before.channel.guild
            self.queue[guild.id] = []
            self.now_playing.pop(guild.id, None)


def setup(bot):
    bot.add_cog(MusicCog(bot))
