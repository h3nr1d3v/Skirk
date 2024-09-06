import discord
from discord.ext import commands
import asyncio
import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from async_timeout import timeout
import os
from dotenv import load_dotenv
import aiohttp
import random
import base64

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('music_bot')

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Spotify authentication
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class SpotifySource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data['name']
        self.url = data['external_urls']['spotify']
        self.artist = data['artists'][0]['name']
        self.duration = data['duration_ms'] / 1000  # Convert to seconds

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            track_id = url.split('/')[-1]
            track_info = await loop.run_in_executor(None, sp.track, track_id)

            # We're not actually streaming audio, so we'll use a silent audio source
            source = discord.FFmpegPCMAudio(source='path/to/silent.wav')

            return cls(source, data=track_info)
        except Exception as e:
            logger.error(f"Error in from_url: {e}", exc_info=True)
            return None


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}

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

    async def search_spotify(self, query):
        try:
            results = sp.search(q=query, limit=5)
            tracks = results['tracks']['items']
            return tracks
        except Exception as e:
            logger.error(f"Error in search_spotify: {e}", exc_info=True)
            return []

    async def get_random_image(self):
        async with aiohttp.ClientSession() as session:
            endpoints = ['neko', 'waifu', 'husbando']
            endpoint = random.choice(endpoints)
            async with session.get(f'https://nekos.best/api/v2/{endpoint}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['results'][0]['url']
                else:
                    return None

    async def create_search_results_embed(self, results, image_url):
        embed = discord.Embed(title="Search Results",
                              color=discord.Color.green())
        for i, track in enumerate(results, 1):
            embed.add_field(
                name=f"{i}. {track['name']}", value=f"by {track['artists'][0]['name']}", inline=False)
        embed.set_image(url=image_url)
        embed.set_footer(
            text="Type the number to select a song, or 'cancel' to cancel.")
        return embed

    async def create_now_playing_embed(self, song, image_url):
        embed = discord.Embed(
            title="Now Playing", description=f"{song.title} by {song.artist}", color=discord.Color.green())
        embed.add_field(
            name="Duration", value=f"{int(song.duration // 60)}:{int(song.duration % 60):02d}")
        embed.set_image(url=image_url)
        embed.set_footer(
            text="Use !pause, !resume, or !skip to control playback")
        return embed

    @commands.command()
    async def play(self, ctx, *, query):
        if not await self.ensure_voice(ctx):
            return

        async with ctx.typing():
            try:
                async with timeout(10):
                    results = await self.search_spotify(query)

                    if not results:
                        return await ctx.send("No results found. Please try a different search query.")

                    image_url = await self.get_random_image()
                    embed = await self.create_search_results_embed(results, image_url)
                    await ctx.send(embed=embed)

                try:
                    msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel and (m.content.isdigit() or m.content.lower() == 'cancel'), timeout=30.0)
                except asyncio.TimeoutError:
                    return await ctx.send("Song selection timed out.")

                if msg.content.lower() == 'cancel':
                    return await ctx.send("Song selection cancelled.")

                try:
                    choice = int(msg.content)
                    if choice < 1 or choice > len(results):
                        return await ctx.send("Invalid choice. Please try again.")
                except ValueError:
                    return await ctx.send("Invalid input. Please enter a number.")

                selected_song = results[choice - 1]
                player = await SpotifySource.from_url(selected_song['external_urls']['spotify'], loop=self.bot.loop)

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
            await ctx.send(f'Added to queue: {player.title} by {player.artist}')

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
        await self.update_now_playing(ctx)

    async def update_now_playing(self, ctx):
        if ctx.guild.id in self.now_playing and self.now_playing[ctx.guild.id]:
            player = self.now_playing[ctx.guild.id]
            image_url = await self.get_random_image()
            embed = await self.create_now_playing_embed(player, image_url)
            message = await ctx.send(embed=embed)
            await self.animate_now_playing(message, player.duration)

    async def animate_now_playing(self, message, duration):
        animations = [
            "▶️ ⏸️ ⏭️",
            "🎵 🎶 🎵",
            "🔊 🔉 🔈",
            "🎧 🎤 🎹",
        ]
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < duration:
            for animation in animations:
                embed = message.embeds[0]
                embed.set_author(name=animation)
                elapsed = int(asyncio.get_event_loop().time() - start_time)
                embed.set_footer(
                    text=f"{elapsed // 60}:{elapsed % 60:02d} / {int(duration // 60)}:{int(duration % 60):02d}")
                await message.edit(embed=embed)
                await asyncio.sleep(1)
                if asyncio.get_event_loop().time() - start_time >= duration:
                    break

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
        queue_list = "\n".join(f"{i+1}. {song.title} by {song.artist}" for i,
                               song in enumerate(self.queue[ctx.guild.id]))
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
            await self.update_now_playing(ctx)
        else:
            await ctx.send("Nothing is playing right now.")


def setup(bot):
    bot.add_cog(MusicCog(bot))
