import aiohttp, config, asyncio
from discord.ext import commands
from models import Transactions, Products, Role_Products, Role_Transactions


class paypal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.temp_token = None
        self.bot.loop.create_task(self.token_refresher())
        self.bot.loop.create_task(self.product_sender())
        self.bot.loop.create_task(self.role_sender())

    async def role_sender(self):
        records = await Role_Transactions.filter(paid=False).all()
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
                            product = await Role_Products.get(role_id=t.role_id)
                        except:
                            continue
                        guild = self.bot.get_guild(product.guild_id)
                        if guild:
                            role = guild.get_role(product.role_id)
                            if role:
                                try:
                                    member = guild.get_member(t.user_id) or await guild.fetch_member(t.user_id)
                                except:
                                    continue
                                try:
                                    await member.add_roles(role)
                                except:
                                    continue
        await asyncio.sleep(20)
        self.bot.loop.create_task(self.role_sender())

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
