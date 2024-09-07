import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
import urllib.parse
import urllib.request
import re
from aiohttp import ClientSession
import random

load_dotenv()

youtube_base_url = 'https://www.youtube.com/'
youtube_results_url = youtube_base_url + 'results?'
youtube_watch_url = youtube_base_url + 'watch?v='

yt_dl_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0"
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.25"'
}

ytdl = yt_dlp.YoutubeDL(yt_dl_options)


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.voice_clients = {}
        self.current_songs = {}
        self.loop = {}
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    async def send_banner(self, ctx, track):
        async with ClientSession(headers={'User-Agent': random.choice(self.user_agents)}) as session:
            async with session.get(f'https://nekos.best/api/v2/music') as resp:
                data = await resp.json()
                embed = discord.Embed(
                    title="Now Playing", description=f"{track['title']}")
                if 'results' in data and len(data['results']) > 0:
                    embed.set_image(url=data['results'][0]['url'])
                await ctx.send(embed=embed)

    async def play_next(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            if self.loop.get(ctx.guild.id, False):
                self.queues[ctx.guild.id].append(
                    self.current_songs[ctx.guild.id])
            next_song = self.queues[ctx.guild.id].pop(0)
            await self.play_song(ctx, next_song)
        else:
            await ctx.send("Queue is empty. Playback finished.")

    async def play_song(self, ctx, song):
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song['url'], download=False))

            song_url = data['url']
            player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

            if ctx.guild.id in self.voice_clients:
                self.voice_clients[ctx.guild.id].play(
                    player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                self.current_songs[ctx.guild.id] = song
                await self.send_banner(ctx, song)
            else:
                await ctx.send("Not connected to a voice channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    async def get_youtube_results(self, query):
        search_query = urllib.parse.urlencode({'search_query': query})
        content = urllib.request.urlopen(youtube_results_url + search_query)
        search_results = re.findall(
            r'/watch\?v=(.{11})', content.read().decode())
        return search_results[:5]  # Return only the first 5 results

    async def get_video_info(self, video_id):
        url = youtube_watch_url + video_id
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return {
            'url': url,
            'title': data['title'],
            'duration': data['duration'],
            'uploader': data['uploader']
        }

    @commands.command(name='play')
    async def play(self, ctx, *, query):
        await asyncio.sleep(random.uniform(1, 3))  # Add a random delay
        if ctx.author.voice is None:
            await ctx.send("You need to be in a voice channel to use this command.")
            return

        if ctx.guild.id not in self.voice_clients:
            voice_client = await ctx.author.voice.channel.connect()
            self.voice_clients[ctx.guild.id] = voice_client

        search_results = await self.get_youtube_results(query)
        if not search_results:
            await ctx.send("No results found.")
            return

        # Get info for each video
        videos = []
        for i, video_id in enumerate(search_results, 1):
            video_info = await self.get_video_info(video_id)
            videos.append(video_info)
            await ctx.send(f"{i}. {video_info['title']} - {video_info['uploader']} ({video_info['duration']} seconds)")

        # Ask user to choose a video
        await ctx.send("Please choose a video by entering a number from 1 to 5.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 5

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("You didn't choose a video in time.")
            return

        chosen_video = videos[int(msg.content) - 1]

        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []

        self.queues[ctx.guild.id].append(chosen_video)

        if not self.voice_clients[ctx.guild.id].is_playing():
            await self.play_song(ctx, chosen_video)
        else:
            await ctx.send(f"Added to queue: {chosen_video['title']}")

    @commands.command(name='pause')
    async def pause(self, ctx):
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            self.voice_clients[ctx.guild.id].pause()
            await ctx.send("Music paused.")

    @commands.command(name='resume')
    async def resume(self, ctx):
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_paused():
            self.voice_clients[ctx.guild.id].resume()
            await ctx.send("Resuming music.")

    @commands.command(name='skip')
    async def skip(self, ctx):
        if ctx.guild.id in self.voice_clients and self.voice_clients[ctx.guild.id].is_playing():
            self.voice_clients[ctx.guild.id].stop()
            await ctx.send("Skipped to next track.")

    @commands.command(name='queue')
    async def queue(self, ctx):
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            queue_list = "\n".join(
                [f"{i+1}. {track['title']}" for i, track in enumerate(self.queues[ctx.guild.id])])
            await ctx.send(f"Current Queue:\n{queue_list}")
        else:
            await ctx.send("Queue is empty.")

    @commands.command(name='clear_queue')
    async def clear_queue(self, ctx):
        if ctx.guild.id in self.queues:
            self.queues[ctx.guild.id].clear()
            await ctx.send("Queue cleared!")
        else:
            await ctx.send("There is no queue to clear")

    @commands.command(name='leave')
    async def leave(self, ctx):
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            await ctx.send("Disconnected from voice channel.")

    @commands.command(name='join')
    async def join(self, ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.guild.id not in self.voice_clients:
                voice_client = await channel.connect()
                self.voice_clients[ctx.guild.id] = voice_client
                await ctx.send(f"Joined {channel.name}")
            else:
                await ctx.send("Already connected to a voice channel.")
        else:
            await ctx.send("You need to be in a voice channel to use this command.")

    @commands.command(name='loop')
    async def loop(self, ctx):
        self.loop[ctx.guild.id] = not self.loop.get(ctx.guild.id, False)
        await ctx.send(f"Loop {'enabled' if self.loop[ctx.guild.id] else 'disabled'}.")

    @commands.command(name='reboot')
    async def reboot(self, ctx):
        if ctx.guild.id in self.current_songs:
            await self.play_song(ctx, self.current_songs[ctx.guild.id])
            await ctx.send("Rebooting current song.")
        else:
            await ctx.send("No song is currently playing.")


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
