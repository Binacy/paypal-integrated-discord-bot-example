import aiohttp, core.config as config, asyncio
from discord.ext import commands


class paypal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.temp_token = None
        self.bot.loop.create_task(self.token_refresher())

    async def token_refresher(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sandbox.paypal.com/v1/oauth2/token",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en_US",
                },
                auth=aiohttp.BasicAuth(
                    config.paypal_client_id,
                    config.paypal_client_secret,
                ),
                data="grant_type=client_credentials",
            ) as resp:
                sleep = (await resp.json())["expires_in"]
                self.bot.temp_token = (await resp.json())["access_token"]
        await asyncio.sleep(sleep)
        self.bot.loop.create_task(self.token_refresher())


async def setup(bot):
    await bot.add_cog(paypal(bot))
