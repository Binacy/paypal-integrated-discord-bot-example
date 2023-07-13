from discord.ext import commands
from datetime import datetime
from models import Timers
import asyncio


class timers_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._have_data = asyncio.Event()
        self._current_timer = None
        self._task = self.bot.loop.create_task(self.dispatch_timers())

    def cog_unload(self):
        self._task.cancel()

    async def get_active_timer(self):
        return (
            await Timers.filter(expires__lte=datetime.now(tz=self.bot.ist))
            .order_by("expires")
            .first()
        ) or (
            await Timers.filter(expires__gte=datetime.now(tz=self.bot.ist))
            .order_by("expires")
            .first()
        )

    async def wait_for_active_timers(self):
        timer = await self.get_active_timer()
        if timer is not None:
            self._have_data.set()
            return timer

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()
        return await self.get_active_timer()

    async def call_timer(self, timer):
        await Timers.filter(pk=timer.id, expires=timer.expires).delete()
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                timer = self._current_timer = await self.wait_for_active_timers()
                now = datetime.now(tz=self.bot.ist)

                if timer.expires >= now:
                    to_sleep = (timer.expires - now).total_seconds()
                    await asyncio.sleep(to_sleep)

                await self.call_timer(timer)
        except asyncio.CancelledError:
            raise
        except OSError:
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def short_timer_optimisation(self, seconds, timer):
        await asyncio.sleep(seconds)
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def create_timer(
        self,
        expires=None,
        event: str = None,
        author_id: int = None,
        channel_id: int = None,
        guild_id: int = None,
        message: str = None,
        created_at=None,
        message_id: int = None,
        jump_url: str = None,
    ):
        created_at = created_at or datetime.now(tz=self.bot.ist)
        delta = (expires - created_at).total_seconds()
        timer = Timers(
            expires=expires,
            event=event,
            author_id=author_id,
            channel_id=channel_id,
            guild_id=guild_id,
            message=message,
            created_at=created_at,
            message_id=message_id,
            jump_url=jump_url,
        )
        if delta <= 60:
            self.bot.loop.create_task(self.short_timer_optimisation(delta, timer))
            return
        await timer.save()

        if delta <= (86400 * 40):
            self._have_data.set()

        if self._current_timer and expires < self._current_timer.expires:
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

        return


async def setup(bot):
    await bot.add_cog(timers_cog(bot))
