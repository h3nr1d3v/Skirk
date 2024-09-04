import discord
from discord.ext import commands
import requests


class AnimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def waifu(self, ctx):
        """Fetch a random waifu image from Nekos Best"""
        url = "https://nekos.best/api/v2/waifu"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch waifu image. Please try again later.")

    @commands.command()
    async def neko(self, ctx):
        """Fetch a random neko image from Nekos Best"""
        url = "https://nekos.best/api/v2/neko"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch neko image. Please try again later.")

    @commands.command()
    async def trap(self, ctx):
        """Fetch a random trap image from Nekos Best"""
        url = "https://nekos.best/api/v2/trap"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch trap image. Please try again later.")

    @commands.command()
    async def blowjob(self, ctx):
        """Fetch a random blowjob image from Nekos Best"""
        url = "https://nekos.best/api/v2/blowjob"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch blowjob image. Please try again later.")

    @commands.command()
    async def hentai(self, ctx):
        """Fetch a random hentai image from Nekos Best"""
        url = "https://nekos.best/api/v2/hentai"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch hentai image. Please try again later.")

    @commands.command()
    async def lewd(self, ctx):
        """Fetch a random lewd image from Nekos Best"""
        url = "https://nekos.best/api/v2/lewd"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            image_url = data["results"][0]["url"]
            await ctx.send(image_url)
        else:
            await ctx.send("Failed to fetch lewd image. Please try again later.")

    @commands.command()
    async def anime(self, ctx, *, anime_name: str):
        """Fetch information about an anime using Jikan API"""
        url = f"https://api.jikan.moe/v4/anime?q={anime_name}&limit=1"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data['data']:
                anime = data['data'][0]
                title = anime.get('title', 'Unknown Title')
                synopsis = anime.get('synopsis', 'No synopsis available.')
                image_url = anime.get('images', {}).get(
                    'jpg', {}).get('large_image_url', '')

                embed = discord.Embed(
                    title=title, description=synopsis, color=discord.Color.purple())
                if image_url:
                    embed.set_image(url=image_url)

                await ctx.send(embed=embed)
            else:
                await ctx.send("No anime found with that name.")
        else:
            await ctx.send("Failed to fetch anime information. Please try again later.")

# Remember to add this cog in your main.py file:
# bot.add_cog(AnimeCog(bot))
