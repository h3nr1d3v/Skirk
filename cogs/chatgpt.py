import discord
from discord.ext import commands
import openai
import os


class ChatGPTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        openai.api_key = os.getenv("OPENAI_API_KEY")

    @commands.command()
    async def ask(self, ctx, *, question):
        """Ask a question to ChatGPT"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Usa el modelo de ChatGPT más reciente
                messages=[
                    {"role": "user", "content": question}
                ],
                max_tokens=150
            )
            answer = response.choices[0].message['content'].strip()
            await ctx.send(f"ChatGPT says: {answer}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")