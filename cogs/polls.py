import discord
from discord.ext import commands
import asyncio
from typing import List
import aiohttp
import json


class PollsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}
        # Replace with your actual API key
        self.strawpoll_api_key = "YOUR_STRAWPOLL_API_KEY"
        self.strawpoll_api_url = "https://api.strawpoll.com/v3/polls"

    @commands.group(invoke_without_command=True)
    async def poll(self, ctx, question: str, *options: str):
        """Create a poll with multiple options"""
        if len(options) > 10:
            await ctx.send("Solo puedes tener hasta 10 opciones.")
            return

        if len(options) < 2:
            await ctx.send("Necesitas al menos 2 opciones.")
            return

        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                     '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description.append(f'\n {reactions[x]} {option}')

        embed = discord.Embed(title=question, description=''.join(
            description), color=discord.Color.blue())
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")

        react_message = await ctx.send(embed=embed)

        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

        self.active_polls[react_message.id] = {
            'question': question,
            'options': options,
            'reactions': reactions[:len(options)],
            'creator': ctx.author.id,
            'channel': ctx.channel.id
        }

        await ctx.message.delete()

    @poll.command(name="end")
    async def end_poll(self, ctx, message_id: int):
        """End a poll and display the results"""
        if message_id not in self.active_polls:
            await ctx.send("No se encontró una encuesta activa con ese ID.")
            return

        poll_data = self.active_polls[message_id]
        channel = self.bot.get_channel(poll_data['channel'])
        message = await channel.fetch_message(message_id)

        results = await self.tally_results(message, poll_data['reactions'])

        embed = discord.Embed(
            title=f"Resultados de la encuesta: {poll_data['question']}", color=discord.Color.green())

        for option, (reaction, count) in zip(poll_data['options'], results):
            embed.add_field(name=f"{reaction} {option}",
                            value=f"{count} votos", inline=False)

        await ctx.send(embed=embed)
        del self.active_polls[message_id]

    @commands.command()
    async def quickpoll(self, ctx, *, question: str):
        """Create a quick yes/no poll"""
        embed = discord.Embed(title="Encuesta Rápida",
                              description=question, color=discord.Color.blue())
        embed.set_footer(text=f"Encuesta creada por {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')
        await ctx.message.delete()

    @commands.command()
    async def strawpoll(self, ctx, title: str, *options: str):
        """Create a strawpoll"""
        if len(options) < 2:
            await ctx.send("Necesitas al menos 2 opciones para crear una encuesta.")
            return

        try:
            poll = await self.create_strawpoll(title, list(options))
            await ctx.send(f"He creado una encuesta en StrawPoll: {poll['url']}")
        except Exception as e:
            await ctx.send(f"Hubo un error al crear la encuesta en StrawPoll: {str(e)}")

    async def create_strawpoll(self, title: str, options: List[str]) -> dict:
        """Create a strawpoll using their API"""
        payload = {
            "title": title,
            "options": options,
            "multi": False
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.strawpoll_api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.strawpoll_api_url, data=json.dumps(payload), headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "url": f"https://strawpoll.com/{data['id']}",
                        "admin_url": f"https://strawpoll.com/{data['id']}/results"
                    }
                else:
                    raise Exception(
                        f"Error en la API de StrawPoll: {response.status}")

    async def tally_results(self, message: discord.Message, reactions: List[str]) -> List[tuple]:
        """Tally the results of a poll"""
        results = []
        for reaction in reactions:
            reaction_count = discord.utils.get(
                message.reactions, emoji=reaction)
            count = reaction_count.count - 1 if reaction_count else 0
            results.append((reaction, count))
        return results


async def setup(bot):
    await bot.add_cog(PollsCog(bot))
