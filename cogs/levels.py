import discord
from discord.ext import commands
import json
import asyncio
import random
from datetime import datetime
import aiohttp


class LevelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels = self.load_levels()
        self.xp_cooldown = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.user)
        self.save_task = asyncio.create_task(self.auto_save())
        self.session = aiohttp.ClientSession()
        self.image_cache = {}
        self.cache_expiry = {}

    def cog_unload(self):
        self.save_task.cancel()
        asyncio.create_task(self.session.close())

    def load_levels(self):
        try:
            with open('levels.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_levels(self):
        with open('levels.json', 'w') as f:
            json.dump(self.levels, f, indent=4)

    async def auto_save(self):
        while not self.bot.is_closed():
            self.save_levels()
            await asyncio.sleep(300)  # Save every 5 minutes

    def get_level_xp(self, level):
        return 5 * (level ** 2) + 50 * level + 100

    def get_level_from_xp(self, xp):
        level = 0
        while xp >= self.get_level_xp(level):
            xp -= self.get_level_xp(level)
            level += 1
        return level

    async def fetch_anime_image(self):
        current_time = datetime.now()
        if 'anime' in self.image_cache and (current_time - self.cache_expiry['anime']).total_seconds() < 3600:
            return self.image_cache['anime']

        url = "https://nekos.best/api/v2/neko"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                image_url = data["results"][0]["url"]
                self.image_cache['anime'] = image_url
                self.cache_expiry['anime'] = current_time
                return image_url
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bucket = self.xp_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return

        author_id = str(message.author.id)
        if author_id not in self.levels:
            self.levels[author_id] = {
                "xp": 0, "last_message": datetime.utcnow().isoformat()}

        xp_gain = random.randint(15, 25)
        self.levels[author_id]["xp"] += xp_gain
        self.levels[author_id]["last_message"] = datetime.utcnow().isoformat()

        current_level = self.get_level_from_xp(self.levels[author_id]["xp"])
        previous_level = self.get_level_from_xp(
            self.levels[author_id]["xp"] - xp_gain)

        if current_level > previous_level:
            image_url = await self.fetch_anime_image()
            embed = discord.Embed(
                title=f"🎉 Level Up! 🎉",
                description=f"Congratulations {message.author.mention}! You've reached level {current_level}!",
                color=discord.Color.gold()
            )
            embed.add_field(name="New Level", value=str(
                current_level), inline=True)
            embed.add_field(name="Total XP", value=str(
                self.levels[author_id]["xp"]), inline=True)
            if image_url:
                embed.set_image(url=image_url)
            embed.set_footer(
                text="Keep chatting to earn more XP and level up!")
            await message.channel.send(embed=embed)

    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        """Check your or someone else's level"""
        member = member or ctx.author
        member_id = str(member.id)

        if member_id not in self.levels:
            await ctx.send("This user hasn't earned any XP yet.")
            return

        xp = self.levels[member_id]["xp"]
        level = self.get_level_from_xp(xp)
        xp_for_next_level = self.get_level_xp(level)
        progress = xp - sum(self.get_level_xp(i) for i in range(level))

        embed = discord.Embed(
            title=f"{member.name}'s Level", color=discord.Color.blue())
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(
            name="XP", value=f"{xp}/{xp_for_next_level}", inline=True)
        embed.add_field(name="Rank", value=self.get_rank(
            member_id), inline=True)
        embed.add_field(name="Progress to Next Level",
                        value=f"{progress}/{xp_for_next_level}", inline=False)
        embed.set_footer(text=f"Keep chatting to earn more XP!")

        image_url = await self.fetch_anime_image()
        if image_url:
            embed.set_thumbnail(url=image_url)

        await ctx.send(embed=embed)

    def get_rank(self, member_id):
        sorted_levels = sorted(self.levels.items(),
                               key=lambda x: x[1]["xp"], reverse=True)
        for i, (id, _) in enumerate(sorted_levels):
            if id == member_id:
                return i + 1
        return "N/A"

    @commands.command()
    async def leaderboard(self, ctx):
        """Display the XP leaderboard"""
        sorted_levels = sorted(self.levels.items(),
                               key=lambda x: x[1]["xp"], reverse=True)[:10]

        embed = discord.Embed(title="XP Leaderboard",
                              color=discord.Color.gold())
        for i, (id, data) in enumerate(sorted_levels):
            member = ctx.guild.get_member(int(id))
            if member:
                embed.add_field(
                    name=f"{i+1}. {member.name}",
                    value=f"Level: {self.get_level_from_xp(data['xp'])} | XP: {data['xp']}",
                    inline=False
                )

        image_url = await self.fetch_anime_image()
        if image_url:
            embed.set_thumbnail(url=image_url)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def add_xp(self, ctx, member: discord.Member, xp: int):
        """Add XP to a user (Admin only)"""
        member_id = str(member.id)
        if member_id not in self.levels:
            self.levels[member_id] = {
                "xp": 0, "last_message": datetime.utcnow().isoformat()}

        old_level = self.get_level_from_xp(self.levels[member_id]["xp"])
        self.levels[member_id]["xp"] += xp
        new_level = self.get_level_from_xp(self.levels[member_id]["xp"])

        await ctx.send(f"Added {xp} XP to {member.mention}.")

        if new_level > old_level:
            image_url = await self.fetch_anime_image()
            embed = discord.Embed(
                title=f"🎉 Level Up! 🎉",
                description=f"{member.mention} has reached level {new_level}!",
                color=discord.Color.gold()
            )
            if image_url:
                embed.set_image(url=image_url)
            await ctx.send(embed=embed)

        self.save_levels()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_xp(self, ctx, member: discord.Member, xp: int):
        """Remove XP from a user (Admin only)"""
        member_id = str(member.id)
        if member_id in self.levels:
            self.levels[member_id]["xp"] = max(
                0, self.levels[member_id]["xp"] - xp)
            await ctx.send(f"Removed {xp} XP from {member.mention}.")
            self.save_levels()
        else:
            await ctx.send(f"{member.mention} doesn't have any XP yet.")

    @commands.command()
    async def xp_stats(self, ctx):
        """Display XP statistics"""
        total_xp = sum(data["xp"] for data in self.levels.values())
        total_users = len(self.levels)
        avg_xp = total_xp / total_users if total_users > 0 else 0

        embed = discord.Embed(title="XP Statistics",
                              color=discord.Color.green())
        embed.add_field(name="Total XP", value=str(total_xp), inline=True)
        embed.add_field(name="Total Users", value=str(
            total_users), inline=True)
        embed.add_field(name="Average XP", value=f"{avg_xp:.2f}", inline=True)

        image_url = await self.fetch_anime_image()
        if image_url:
            embed.set_thumbnail(url=image_url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(LevelsCog(bot))
