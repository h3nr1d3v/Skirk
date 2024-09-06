import discord
from discord.ext import commands
import random
import asyncio
import json
import os


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_questions = self.load_trivia_questions()
        self.hangman_words = self.load_hangman_words()
        self.user_scores = self.load_user_scores()

    def load_trivia_questions(self):
        try:
            with open('trivia_questions.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {"question": "What is the capital of France?", "answer": "Paris"},
                {"question": "Who painted the Mona Lisa?",
                    "answer": "Leonardo da Vinci"},
                {"question": "What is the largest planet in our solar system?",
                    "answer": "Jupiter"},
            ]

    def load_hangman_words(self):
        try:
            with open('hangman_words.txt', 'r') as f:
                return [word.strip().lower() for word in f.readlines()]
        except FileNotFoundError:
            return ["python", "programming", "computer", "algorithm", "database", "network", "software"]

    def save_user_scores(self):
        with open('user_scores.json', 'w') as f:
            json.dump(self.user_scores, f)

    def load_user_scores(self):
        try:
            with open('user_scores.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @commands.command()
    async def rps(self, ctx, player_choice: str):
        """Play Rock Paper Scissors"""
        choices = ["rock", "paper", "scissors"]
        if player_choice.lower() not in choices:
            return await ctx.send("Invalid choice. Please choose rock, paper, or scissors.")

        bot_choice = random.choice(choices)

        embed = discord.Embed(title="Rock Paper Scissors",
                              color=discord.Color.blue())
        embed.add_field(name="Your Choice",
                        value=player_choice.capitalize(), inline=True)
        embed.add_field(name="Bot's Choice",
                        value=bot_choice.capitalize(), inline=True)

        if player_choice.lower() == bot_choice:
            result = "It's a tie!"
        elif (player_choice.lower() == "rock" and bot_choice == "scissors") or \
             (player_choice.lower() == "paper" and bot_choice == "rock") or \
             (player_choice.lower() == "scissors" and bot_choice == "paper"):
            result = "You win!"
            self.update_score(ctx.author.id, 1)
        else:
            result = "I win!"

        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

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
                self.update_score(ctx.author.id, 6 - i)
                return await ctx.send(f"Congratulations! You guessed the number in {i+1} tries!")

            if int(guess.content) > number:
                await ctx.send("Too high!")
            else:
                await ctx.send("Too low!")

        await ctx.send(f"Sorry, you've run out of guesses. The number was {number}.")

    @commands.command()
    async def trivia(self, ctx):
        """Play a trivia game"""
        question = random.choice(self.trivia_questions)
        await ctx.send(f"Trivia Time! {question['question']}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            answer = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send(f"Sorry, you took too long. The answer was {question['answer']}.")

        if answer.content.lower() == question['answer'].lower():
            self.update_score(ctx.author.id, 2)
            await ctx.send("Correct! Well done!")
        else:
            await ctx.send(f"Sorry, that's incorrect. The correct answer was {question['answer']}.")

    @commands.command()
    async def hangman(self, ctx):
        """Play Hangman"""
        word = random.choice(self.hangman_words)
        guessed = set()
        tries = 6

        def display_word():
            return ''.join(letter if letter in guessed else '_' for letter in word)

        await ctx.send("Let's play Hangman! Guess the word by suggesting letters.")
        await ctx.send(display_word())

        while tries > 0:
            await ctx.send(f"You have {tries} tries left. Guess a letter:")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()

            try:
                guess = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                return await ctx.send(f"Sorry, you took too long. The word was {word}.")

            letter = guess.content.lower()

            if letter in guessed:
                await ctx.send("You already guessed that letter!")
            elif letter in word:
                guessed.add(letter)
                await ctx.send("Correct guess!")
            else:
                tries -= 1
                await ctx.send("Incorrect guess!")

            current = display_word()
            await ctx.send(current)

            if '_' not in current:
                self.update_score(ctx.author.id, tries + 1)
                return await ctx.send(f"Congratulations! You guessed the word: {word}")

        await ctx.send(f"Sorry, you've run out of tries. The word was {word}.")

    @commands.command()
    async def coin(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="Coin Flip", description=f"The coin landed on: **{result}**", color=discord.Color.gold())
        await ctx.send(embed=embed)

    @commands.command(name="game_leaderboard")
    async def game_leaderboard(self, ctx):
        """Display the game leaderboard"""
        sorted_scores = sorted(self.user_scores.items(),
                               key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title="Game Leaderboard",
                              color=discord.Color.gold())

        for i, (user_id, score) in enumerate(sorted_scores[:10], start=1):
            user = self.bot.get_user(int(user_id))
            if user:
                embed.add_field(name=f"{i}. {user.name}",
                                value=f"Score: {score}", inline=False)

        await ctx.send(embed=embed)

    def update_score(self, user_id, points):
        if str(user_id) not in self.user_scores:
            self.user_scores[str(user_id)] = 0
        self.user_scores[str(user_id)] += points
        self.save_user_scores()


def setup(bot):
    bot.add_cog(GamesCog(bot))
