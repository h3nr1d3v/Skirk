import discord
from discord.ext import commands
import asyncio
import datetime
import pytz


class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        # Usar asyncio.create_task en lugar de self.bot.loop.create_task
        self.check_reminders_task = asyncio.create_task(self.check_reminders())

    async def check_reminders(self):
        while not self.bot.is_closed():
            now = datetime.datetime.now(pytz.UTC)
            reminders_to_remove = []
            for reminder in self.reminders:
                if reminder['time'] <= now:
                    channel = self.bot.get_channel(reminder['channel_id'])
                    if channel:
                        await channel.send(f"{reminder['user'].mention}, Recordatorio: {reminder['message']}")
                    reminders_to_remove.append(reminder)
            for reminder in reminders_to_remove:
                self.reminders.remove(reminder)
            await asyncio.sleep(60)  # Check every minute

    @commands.group(invoke_without_command=True)
    async def remind(self, ctx, time: str, *, reminder: str):
        """Set a reminder"""
        try:
            when = self.parse_time(time)
        except ValueError:
            return await ctx.send("Formato de tiempo inválido. Usa un número seguido de 's', 'm', 'h', o 'd'.")

        reminder_time = datetime.datetime.now(pytz.UTC) + when
        self.reminders.append({
            'user': ctx.author,
            'channel_id': ctx.channel.id,
            'time': reminder_time,
            'message': reminder
        })

        await ctx.send(f"Te recordaré sobre '{reminder}' en {time}.")

    @remind.command(name="list")
    async def remind_list(self, ctx):
        """List all your active reminders"""
        user_reminders = [r for r in self.reminders if r['user'] == ctx.author]
        if not user_reminders:
            return await ctx.send("No tienes recordatorios activos.")

        embed = discord.Embed(
            title="Tus recordatorios activos", color=discord.Color.blue())
        for i, reminder in enumerate(user_reminders, 1):
            embed.add_field(
                name=f"Recordatorio {i}",
                value=f"Mensaje: {reminder['message']}\nTiempo: {reminder['time'].strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
        await ctx.send(embed=embed)

    @remind.command(name="delete")
    async def remind_delete(self, ctx, index: int):
        """Delete a specific reminder"""
        user_reminders = [r for r in self.reminders if r['user'] == ctx.author]
        if not user_reminders:
            return await ctx.send("No tienes recordatorios activos.")

        if 1 <= index <= len(user_reminders):
            reminder = user_reminders[index - 1]
            self.reminders.remove(reminder)
            await ctx.send(f"Recordatorio eliminado: '{reminder['message']}'")
        else:
            await ctx.send("Índice de recordatorio inválido.")

    @commands.command()
    async def event(self, ctx, date: str, time: str, *, event_name: str):
        """Schedule an event"""
        try:
            event_datetime = datetime.datetime.strptime(
                f"{date} {time}", "%Y-%m-%d %H:%M")
            event_datetime = pytz.timezone('UTC').localize(event_datetime)
        except ValueError:
            return await ctx.send("Formato de fecha o tiempo inválido. Usa YYYY-MM-DD para la fecha y HH:MM para el tiempo.")

        now = datetime.datetime.now(pytz.UTC)

        if event_datetime < now:
            return await ctx.send("¡No puedes programar un evento en el pasado!")

        self.reminders.append({
            'user': ctx.author,
            'channel_id': ctx.channel.id,
            'time': event_datetime,
            'message': f"@everyone Recordatorio de evento: {event_name} está comenzando ahora!"
        })
        await ctx.send(f"Evento '{event_name}' programado para {event_datetime}")

    @staticmethod
    def parse_time(time: str) -> datetime.timedelta:
        time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        time_unit = time[-1]
        time_value = time[:-1]

        if not time_value.isdigit() or time_unit not in time_dict:
            raise ValueError("Invalid time format")

        return datetime.timedelta(seconds=int(time_value) * time_dict[time_unit])


async def setup(bot):
    await bot.add_cog(RemindersCog(bot))
