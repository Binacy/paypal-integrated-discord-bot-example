import aiohttp, core.config as config, asyncio
from discord.ext import commands
from models import Transactions, Products


class paypal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.temp_token = None
        self.bot.loop.create_task(self.token_refresher())
        self.bot.loop.create_task(self.product_sender())

    async def product_sender(self):
        records = await Transactions.filter(paid=False).all()
        for t in records:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.sandbox.paypal.com/v2/invoicing/invoices/{t.payapl_id}"
                    ) as resp:
                    data = await resp.json()
                    if data["status"] == "PAID":
                        t.paid = True
                        await t.save()
                        try:
                            product = await Products.get(id=t.product_id)
                        except:
                            continue
                        user = self.bot.get_user(t.user_id) or await self.bot.fetch_user(t.user_id)
                        await user.send(f"Thank you for purchasing {product.name}! Here's your product url: {product.image}")
        await asyncio.sleep(20)
        self.bot.loop.create_task(self.product_sender())

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
