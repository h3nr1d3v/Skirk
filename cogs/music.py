import os
import discord
from discord.ext import commands
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import aiohttp
from discord import FFmpegPCMAudio
from discord.utils import get
import random

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        ))
        self.queue = []
        self.current_song = None
        self.is_playing = False
        self.is_looping = False

    async def get_nekos_image(self, endpoint):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://nekos.best/api/v2/{endpoint}') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['results'][0]['url']
                return None

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You're not connected to a voice channel.")
            return

        voice_channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        else:
            await ctx.voice_client.move_to(voice_channel)

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            self.current_song = None
            self.is_playing = False

    @commands.command()
    async def play(self, ctx, *, query):
        if ctx.voice_client is None:
            await self.join(ctx)

        results = self.spotify.search(q=query, type='track', limit=5)
        tracks = results['tracks']['items']

        if not tracks:
            await ctx.send("No songs found.")
            return

        embed = discord.Embed(title="Search Results",
                              color=discord.Color.blue())
        for i, track in enumerate(tracks, start=1):
            embed.add_field(name=f"{i}. {track['name']} - {track['artists'][0]['name']}",
                            value=f"Duration: {track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
                            inline=False)

        image_url = await self.get_nekos_image('neko')
        if image_url:
            embed.set_image(url=image_url)

        message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(tracks)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            selected_track = tracks[int(msg.content) - 1]
            self.queue.append(selected_track)
            await ctx.send(f"Added to queue: {selected_track['name']} - {selected_track['artists'][0]['name']}")

            if not self.is_playing:
                await self.play_next(ctx)
        except asyncio.TimeoutError:
            await message.delete()
            await ctx.send("Selection timed out.")

    async def play_next(self, ctx):
        if not self.queue:
            self.is_playing = False
            return

        if not self.is_looping:
            self.current_song = self.queue.pop(0)

        ctx.voice_client.play(FFmpegPCMAudio(self.current_song['preview_url']),
                              after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        self.is_playing = True

        embed = discord.Embed(
            title="Now Playing", description=f"{self.current_song['name']} - {self.current_song['artists'][0]['name']}", color=discord.Color.green())
        image_url = await self.get_nekos_image('waifu')
        if image_url:
            embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused ⏸️")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed ▶️")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Skipped ⏭️")
            await self.play_next(ctx)

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            await ctx.send("The queue is empty.")
            return

        embed = discord.Embed(title="Queue", color=discord.Color.blue())
        for i, track in enumerate(self.queue, start=1):
            embed.add_field(name=f"{i}. {track['name']} - {track['artists'][0]['name']}",
                            value=f"Duration: {track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
                            inline=False)

        image_url = await self.get_nekos_image('kitsune')
        if image_url:
            embed.set_image(url=image_url)

        await ctx.send(embed=embed)

    @commands.command()
    async def bucle(self, ctx):
        self.is_looping = not self.is_looping
        await ctx.send(f"Looping is now {'enabled' if self.is_looping else 'disabled'} 🔁")


async def setup(bot):
    await bot.add_cog(Music(bot))
