import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

ffmpeg_options = {
    'options': '-vn'
}

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
    'source_address': None,  # O usa una IP específica si es necesario
    'force-ipv4': False,
    'cachedir': True,  # Habilitar caché puede reducir la frecuencia de las solicitudes
    'extractor_retries': 3,  # Controlar el número de reintentos
    'socket_timeout': 30,
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
            if 'entries' in data:
                data = data['entries'][0]
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except Exception as e:
            print(f"Error in from_url: {e}")
            return None


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel.")
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        if ctx.voice_client is None:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                if player is None:
                    return await ctx.send("Couldn't find the song. Please try again with a different query.")
            except Exception as e:
                return await ctx.send(f"An error occurred: {str(e)}")

            if ctx.guild.id not in self.queue:
                self.queue[ctx.guild.id] = []
            self.queue[ctx.guild.id].append(player)

        if ctx.voice_client and not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f'Added to queue: {player.title}')

    async def play_next(self, ctx):
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            return await ctx.send("Queue is empty. Use !play to add more songs.")

        player = self.queue[ctx.guild.id].pop(0)
        if ctx.voice_client:
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop))
            self.now_playing[ctx.guild.id] = player
            await ctx.send(f'Now playing: {player.title}')
        else:
            await ctx.send("Not connected to a voice channel. Use !join to connect.")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused ⏸️")
        else:
            await ctx.send("Nothing is playing right now. Use !play to add more songs.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed ▶️")
        else:
            await ctx.send("The audio is not paused. Use !play to add more songs.")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped ⏭️")
            await self.play_next(ctx)
        else:
            await ctx.send("Nothing is playing right now. Use !play to add more songs.")

    @commands.command()
    async def queue(self, ctx):
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            return await ctx.send("The queue is empty.")
        queue_list = "\n".join(
            [f"{i+1}. {song.title}" for i, song in enumerate(self.queue[ctx.guild.id])])
        await ctx.send(f"Current queue:\n{queue_list}")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue[ctx.guild.id] = []
            self.now_playing.pop(ctx.guild.id, None)
            await ctx.send("Disconnected from voice channel.")
        else:
            await ctx.send("I'm not connected to a voice channel. Use !join to connect.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user and after.channel is None:
            # Bot was disconnected
            guild = before.channel.guild
            self.queue[guild.id] = []
            self.now_playing.pop(guild.id, None)
