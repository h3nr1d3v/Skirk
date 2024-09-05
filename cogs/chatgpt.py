import discord
from discord.ext import commands
import openai
import os


class ChatGPTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.conversation_history = {}

    @commands.command()
    async def ask(self, ctx, *, question):
        """Ask a question to ChatGPT"""
        try:
            user_id = ctx.author.id
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []

            self.conversation_history[user_id].append(
                {"role": "user", "content": question})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history[user_id],
                max_tokens=150
            )
            answer = response.choices[0].message['content'].strip()
            self.conversation_history[user_id].append(
                {"role": "assistant", "content": answer})

            # Limit conversation history to last 10 messages
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

            embed = discord.Embed(title="ChatGPT Response",
                                  description=answer, color=discord.Color.green())
            embed.set_footer(text=f"Asked by {ctx.author.name}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def clear_chat(self, ctx):
        """Clear your conversation history with ChatGPT"""
        user_id = ctx.author.id
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            await ctx.send("Your conversation history has been cleared.")
        else:
            await ctx.send("You don't have any conversation history to clear.")
