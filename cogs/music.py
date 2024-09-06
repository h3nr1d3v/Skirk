import discord
from discord.ext import commands
import asyncio
import logging
import yt_dlp
import os
from dotenv import load_dotenv
import aiohttp
import random
from asyncio import timeout
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('music_bot')

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# YouTube cookie
YOUTUBE_COOKIE = os.getenv('YOUTUBE_COOKIE')

# Spotify authentication
client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class SpotifySource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('name', 'Unknown Title')
        self.url = data.get('external_urls', {}).get('spotify', '')
        self.artist = ', '.join([artist['name']
                                for artist in data.get('artists', [])])
        self.duration = data.get('duration_ms', 0) / 1000  # Convert to seconds

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            track_id = url.split('/')[-1]
            track_info = sp.track(track_id)

            search_query = f"{track_info['name']} {track_info['artists'][0]['name']}"

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch',
                'noplaylist': True,
                'cookiefile': 'youtube.com_cookies.txt'  # We'll create this file
            }

            # Create a temporary cookie file
            with open('youtube.com_cookies.txt', 'w') as f:
                f.write(YOUTUBE_COOKIE)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                if 'entries' in info:
                    info = info['entries'][0]

            # Remove the temporary cookie file
            os.remove('youtube.com_cookies.txt')

            return cls(discord.FFmpegPCMAudio(info['url'], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), data=track_info)
        except Exception as e:
            logger.error(f"Error in Spotify from_url: {e}", exc_info=True)
            return None


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown Title')
        self.url = data.get('webpage_url', data.get('url', ''))
        self.artist = data.get('uploader', 'Unknown Artist')
        self.duration = data.get('duration', 0)

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            ydl_opts = {
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
                'source_address': '0.0.0.0',
                'cookiefile': 'youtube.com_cookies.txt'  # We'll create this file
            }

            # Create a temporary cookie file
            with open('youtube.com_cookies.txt', 'w') as f:
                f.write(YOUTUBE_COOKIE)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

            # Remove the temporary cookie file
            os.remove('youtube.com_cookies.txt')

            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url']
            return cls(discord.FFmpegPCMAudio(filename, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), data=data)
        except Exception as e:
            logger.error(f"Error in YouTube from_url: {e}", exc_info=True)
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
            results = sp.search(q=query, type='track', limit=5)
            return results['tracks']['items']
        except Exception as e:
            logger.error(f"Error in search_spotify: {e}", exc_info=True)
            return []

    async def search_youtube(self, query):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                'noplaylist': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f"ytsearch5:{query}", download=False)['entries']
            return info
        except Exception as e:
            logger.error(f"Error in search_youtube: {e}", exc_info=True)
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

    async def create_search_results_embed(self, results, image_url, is_spotify=True):
        embed = discord.Embed(title="Search Results",
                              color=discord.Color.green())
        for i, track in enumerate(results, 1):
            if is_spotify:
                embed.add_field(
                    name=f"{i}. {track['name']}", value=f"by {', '.join([artist['name'] for artist in track['artists']])}", inline=False)
            else:
                embed.add_field(
                    name=f"{i}. {track['title']}", value=f"by {track.get('uploader', 'Unknown')}", inline=False)
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
    async def playsp(self, ctx, *, query):
        if not await self.ensure_voice(ctx):
            return

        async with ctx.typing():
            try:
                async with timeout(10):
                    results = await self.search_spotify(query)

                    if not results:
                        return await ctx.send("No results found. Please try a different search query.")

                    image_url = await self.get_random_image()
                    embed = await self.create_search_results_embed(results, image_url, is_spotify=True)
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
            except Exception as e:
                logger.error(f"Error in playsp command: {e}", exc_info=True)
                return await ctx.send("An error occurred while processing your request. Please try again later.")

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f'Added to queue: {player.title} by {player.artist}')

    @commands.command()
    async def playyt(self, ctx, *, query):
        if not await self.ensure_voice(ctx):
            return

        async with ctx.typing():
            try:
                async with timeout(10):
                    results = await self.search_youtube(query)

                    if not results:
                        return await ctx.send("No results found. Please try a different search query.")

                    image_url = await self.get_random_image()
                    embed = await self.create_search_results_embed(results, image_url, is_spotify=False)
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
                player = await YTDLSource.from_url(selected_song['webpage_url'], loop=self.bot.loop)

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
            await ctx.send("Queue is empty. Use !playsp or !playyt to add more songs.")
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
        """Skips the currently playing song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await self.play_next(ctx)
            await ctx.send("Skipped to next song ⏭️")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command()
    async def leave(self, ctx):
        """Disconnects the bot from the voice channel"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected from voice channel 👋")
        else:
            await ctx.send("I am not connected to a voice channel.")

    @commands.command()
    async def queue(self, ctx):
        """Displays the current queue"""
        if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
            queue_list = "\n".join(
                f"{i + 1}. {player.title} by {player.artist}" for i, player in enumerate(self.queue[ctx.guild.id]))
            await ctx.send(f"Current queue:\n{queue_list}")
        else:
            await ctx.send("The queue is empty.")


def setup(bot):
    bot.add_cog(MusicCog(bot))
