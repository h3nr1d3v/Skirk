import discord
from discord.ext import commands
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from aiohttp import ClientSession
import asyncio
import random
from youtube_dl import YoutubeDL

# Spotify setup
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

spotify_auth = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=spotify_auth)

# YouTube setup
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current = None
        self.loop = False
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    async def search_spotify(self, query):
        results = spotify.search(q=query, type='track', limit=5)
        tracks = results['tracks']['items']
        return tracks

    async def send_banner(self, ctx, tracks):
        async with ClientSession(headers={'User-Agent': random.choice(self.user_agents)}) as session:
            async with session.get(f'https://nekos.best/api/v2/music') as resp:
                data = await resp.json()
                embed = discord.Embed(title="Tracks found", description="\n".join(
                    [f"{i+1}. {track['name']} - {track['artists'][0]['name']}" for i, track in enumerate(tracks)]))
                embed.set_image(url=data['results'][0]['url'])
                await ctx.send(embed=embed)

    async def play_music(self, ctx):
        if not self.queue:
            await ctx.send("No songs in the queue!")
            return

        self.current = self.queue.pop(0)
        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()

        voice_client = ctx.voice_client
        voice_client.stop()

        try:
            query = f"{self.current['name']} {self.current['artists'][0]['name']}"
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(ctx), self.bot.loop))
            await ctx.send(f"Now playing: {self.current['name']} by {self.current['artists'][0]['name']}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    async def play_next(self, ctx):
        if self.loop:
            self.queue.append(self.current)
        if self.queue:
            await self.play_music(ctx)
        else:
            await ctx.send("Queue is empty. Playback finished.")

    @commands.command(name='play')
    async def play(self, ctx, *, query):
        await asyncio.sleep(random.uniform(1, 3))  # Add a random delay
        tracks = await self.search_spotify(query)
        await self.send_banner(ctx, tracks)
        self.queue.append(tracks[0])  # Add first track to the queue
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await self.play_music(ctx)

    @commands.command(name='pause')
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Music paused.")

    @commands.command(name='resume')
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resuming music.")

    @commands.command(name='skip')
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped to next track.")

    @commands.command(name='queue')
    async def queue(self, ctx):
        if self.queue:
            await ctx.send("Current Queue:\n" + "\n".join([f"{i+1}. {track['name']} - {track['artists'][0]['name']}" for i, track in enumerate(self.queue)]))
        else:
            await ctx.send("Queue is empty.")

    @commands.command(name='leave')
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from voice channel.")

    @commands.command(name='join')
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("You need to be in a voice channel to use this command.")

    @commands.command(name='loop')
    async def loop(self, ctx):
        self.loop = not self.loop
        await ctx.send(f"Loop {'enabled' if self.loop else 'disabled'}.")

    @commands.command(name='reboot')
    async def reboot(self, ctx):
        if self.current:
            await self.play_music(ctx)
            await ctx.send("Rebooting current song.")


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
