import discord
from discord.ext import commands
import asyncio
import datetime


class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []

    @commands.command()
    async def remind(self, ctx, time, *, reminder):
        """Set a reminder"""
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        time_unit = time[-1]
        time_value = time[:-1]

        # Validación de formato
        if not time_value.isdigit() or time_unit not in time_dict:
            return await ctx.send("Invalid time format. Please use a number followed by 's', 'm', 'h', or 'd'.")

        reminder_time = int(time_value) * time_dict[time_unit]

        await ctx.send(f"I will remind you about '{reminder}' in {time}.")

        await asyncio.sleep(reminder_time)
        await ctx.send(f"{ctx.author.mention}, you asked me to remind you about: {reminder}")

    @commands.command()
    async def event(self, ctx, date, time, *, event_name):
        """Schedule an event"""
        try:
            event_datetime = datetime.datetime.strptime(
                f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return await ctx.send("Invalid date or time format. Please use YYYY-MM-DD for the date and HH:MM for the time.")

        now = datetime.datetime.now()

        if event_datetime < now:
            return await ctx.send("You can't schedule an event in the past!")

        self.reminders.append((event_datetime, ctx.channel.id, event_name))
        await ctx.send(f"Event '{event_name}' scheduled for {event_datetime}")

        await asyncio.sleep((event_datetime - now).total_seconds())
        await self.bot.get_channel(ctx.channel.id).send(f"@everyone Event reminder: {event_name} is starting now!")

# Remember to add this cog in your main.py file:
# bot.add_cog(RemindersCog(bot))
