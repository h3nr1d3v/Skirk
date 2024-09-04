import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

# Configuración de las opciones de FFmpeg
ffmpeg_options = {
    'options': '-vn'
}

# Configuración de yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # Evita problemas con IPv6
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')  # Extraer el título
        self.url = data.get('url')      # Extraer la URL

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel.")
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a song"""
        if ctx.voice_client is None:
            await ctx.invoke(self.join)

        async with ctx.typing():
            player = await YTDLSource.from_url(query, loop=self.bot.loop)
            if ctx.guild.id not in self.queue:
                self.queue[ctx.guild.id] = []
            self.queue[ctx.guild.id].append(player)

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f'Added to queue: {player.title}')

    async def play_next(self, ctx):
        if not self.queue[ctx.guild.id]:
            return await ctx.send("Queue is empty. Use !play to add more songs.")

        player = self.queue[ctx.guild.id].pop(0)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
            self.play_next(ctx), self.bot.loop))
        self.now_playing[ctx.guild.id] = player
        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def pause(self, ctx):
        """Pauses the currently playing song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused ⏸️")

    @commands.command()
    async def resume(self, ctx):
        """Resumes the currently paused song"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed ▶️")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped ⏭️")
            await self.play_next(ctx)

    @commands.command()
    async def queue(self, ctx):
        """Shows the current queue"""
        if not self.queue[ctx.guild.id]:
            return await ctx.send("The queue is empty.")
        queue_list = "\n".join(
            [f"{i+1}. {song.title}" for i, song in enumerate(self.queue[ctx.guild.id])])
        await ctx.send(f"Current queue:\n{queue_list}")

    @commands.command()
    async def leave(self, ctx):
        """Leaves the voice channel"""
        await ctx.voice_client.disconnect()
        self.queue[ctx.guild.id] = []
        self.now_playing.pop(ctx.guild.id, None)
