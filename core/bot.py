import aiohttp, discord, config
from typing import Union
from discord.ext import commands
from discord import utils as discord_utils
from tortoise import Tortoise

discord_utils.setup_logging()


class ppbot(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

    async def get_context(
        self, origin: Union[discord.Interaction, discord.Message], /, *, cls=commands.Context
    ):
        return await super().get_context(origin, cls=cls)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.NotOwner):
            return
        print(error)

    @property
    def timors(self):
        return self.get_cog("timers_cog")

    @property
    def db(self):
        """to execute raw queries"""
        return Tortoise.get_connection("default")._pool

    async def setup_hook(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        await Tortoise.init(config.tortoise_config)
        await Tortoise.generate_schemas(safe=True)
        for model_name, model in Tortoise.apps.get("models").items():
            setattr(model, "bot", self)
            setattr(self, model_name, model)
        await self.load_extension("ext.cmds")
        await self.load_extension("ext.paypal")
        await self.load_extension("ext.timers")
        await self.load_extension("jishaku")

    async def close(self):
        await Tortoise.close_connections()
        await super().close()
