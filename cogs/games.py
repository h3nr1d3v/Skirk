import discord
from discord.ext import commands
import random


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def rps(self, ctx, player_choice: str):
        """Play Rock Paper Scissors"""
        choices = ["rock", "paper", "scissors"]
        if player_choice.lower() not in choices:
            return await ctx.send("Invalid choice. Please choose rock, paper, or scissors.")

        bot_choice = random.choice(choices)

        if player_choice.lower() == bot_choice:
            result = "It's a tie!"
        elif (player_choice.lower() == "rock" and bot_choice == "scissors") or \
             (player_choice.lower() == "paper" and bot_choice == "rock") or \
             (player_choice.lower() == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "I win!"

        await ctx.send(f"You chose {player_choice}, I chose {bot_choice}. {result}")

    @commands.command()
    async def guess(self, ctx):
        """Play a number guessing game"""
        number = random.randint(1, 100)
        await ctx.send("I'm thinking of a number between 1 and 100. You have 6 tries to guess it!")

        for i in range(6):
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

            try:
                guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                return await ctx.send(f"Sorry, you took too long. The number was {number}.")

            if int(guess.content) == number:
                return await ctx.send(f"Congratulations! You guessed the number in {i+1} tries!")

            if int(guess.content) > number:
                await ctx.send("Too high!")
            else:
                await ctx.send("Too low!")

        await ctx.send(f"Sorry, you've run out of guesses. The number was {number}.")

# Remember to add this cog in your main.py file:
# bot.add_cog(GamesCog(bot))
