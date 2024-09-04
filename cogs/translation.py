import discord
from discord.ext import commands
from googletrans import Translator


class TranslationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command()
    async def translate(self, ctx, lang, *, text):
        """Translate text to a specified language"""
        try:
            translated = self.translator.translate(text, dest=lang)
            embed = discord.Embed(title="Translation",
                                  color=discord.Color.blue())
            embed.add_field(name="Original", value=text, inline=False)
            embed.add_field(
                name=f"Translated to {lang}", value=translated.text, inline=False)
            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send("Invalid language code. Please use ISO 639-1 language codes (e.g., 'en' for English, 'es' for Spanish).")

# Remember to add this cog in your main.py file:
# bot.add_cog(TranslationCog(bot))
