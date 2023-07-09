import discord, aiohttp
from discord.ext import commands
from discord import app_commands
from models import Products, Transactions
from core.utils import ButtonPagination, email_input, prompt


class cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy")
    async def _buy(self, interaction: discord.Interaction, product_id: int = None):
        ctx = await self.bot.get_context(interaction)

        def check(message):
            if message.author == ctx.author and message.channel == ctx.channel:
                return True

        r = await Transactions.filter(user_id=interaction.user.id, paid=False).all()
        if r:
            await interaction.response.send_message(
                "You already have an order pending, please complete that purchase first! Use /order-cancel <transaction id> to cancel it!"
            )
            return
        if product_id:
            try:
                product = await Products.get(id=product_id)
            except:
                await interaction.response.send_message(
                    "Product not found! Use /buy to see all products!"
                )
                return
            if product.stock <= 0:
                await interaction.response.send_message("This product is out of stock!")
                return
            if product.user is not None and product.user != interaction.user.id:
                await interaction.response.send_message("This product is not for you!")
                return
            if product.role is not None and product.role not in [
                r.id for r in interaction.user.roles
            ]:
                await interaction.response.send_message(
                    "You don't have the required role to buy this product!"
                )
                return
            await interaction.response.send_message(
                "Please provide your email address, I'll create an invoice for you!\nPlease send your email only nothing else!"
            )
            email = await email_input(ctx, check)
            confirm = await prompt(
                ctx,
                f"Can you confirm {email} is corrent and you can recieve invoice on this email?",
                author_id=ctx.author.id,
            )
            if not confirm:
                await ctx.channel.send("Alright! Cancelling the order!")
                return
            uid = None
            paypal_data = {
                "detail": {
                    "invoice_number": f"TXN-{interaction.user.id}",
                    "reference": "deal-ref",
                    "currency_code": "USD",
                    "note": "Thank you for your purchase!!!.",
                    "term": "No refunds.",
                },
                "invoicer": {
                    "name": {"given_name": "David", "surname": "Larusso"},
                    "address": {
                        "address_line_1": "1234 First Street",
                        "address_line_2": "337673 Hillside Court",
                        "admin_area_2": "Anytown",
                        "admin_area_1": "CA",
                        "postal_code": "98765",
                        "country_code": "US",
                    },
                    "email_address": "merchant@example.com",
                    "phones": [
                        {
                            "country_code": "001",
                            "national_number": "4085551234",
                            "phone_type": "MOBILE",
                        }
                    ],
                    "website": "www.test.com",
                    "logo_url": "https://example.com/logo.PNG",
                },
                "primary_recipients": [
                    {
                        "billing_info": {
                            "name": {"given_name": "Stephanie", "surname": "Meyers"},
                            "address": {
                                "address_line_1": "1234 Main Street",
                                "admin_area_2": "Anytown",
                                "admin_area_1": "CA",
                                "postal_code": "98765",
                                "country_code": "US",
                            },
                            "email_address": f"{email}",
                            "phones": [
                                {
                                    "country_code": "001",
                                    "national_number": "4884551234",
                                    "phone_type": "HOME",
                                }
                            ],
                        },
                        "shipping_info": {
                            "name": {"given_name": "Stephanie", "surname": "Meyers"},
                            "address": {
                                "address_line_1": "1234 Main Street",
                                "admin_area_2": "Anytown",
                                "admin_area_1": "CA",
                                "postal_code": "98765",
                                "country_code": "US",
                            },
                        },
                    }
                ],
                "items": [
                    {
                        "name": f"{product.name}",
                        "description": f"{product.description}",
                        "quantity": "1",
                        "unit_amount": {
                            "currency_code": "USD",
                            "value": f"{product.price}",
                        },
                        "unit_of_measure": "QUANTITY",
                    }
                ],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api-m.sandbox.paypal.com/v2/invoicing/invoices",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    },
                    data=paypal_data,
                ) as resp:
                    print(await resp.json())
                    return
                    uid = (await resp.json())["id"]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api-m.sandbox.paypal.com/v2/invoicing/invoices/{uid}/send",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                    },
                    data='{ "send_to_invoicer": true }',
                ) as resp:
                    print(f"Invoice sent to {email}!")
            await Transactions.create(
                id=f"TXN-{interaction.user.id}",
                payapl_id=uid,
                user_id=interaction.user.id,
                product_id=product.id,
                amount=product.price,
                product_name=product.name,
            )
            await ctx.channel.send(
                "I've sent you an invoice on your email! Please check your email and pay the invoice, Thanks for purchasing with us!"
            )
            return
        embeds = []
        async for p in Products.all():
            if p.stock <= 0:
                continue
            if p.user is not None and p.user != interaction.user.id:
                continue
            if p.role is not None and p.role not in [
                r.id for r in interaction.user.roles
            ]:
                continue
            embed = discord.Embed(
                color=0x26FCFF, title=p.name, description=p.description
            )
            embed.add_field(name="Price", value=f"{p.price}$")
            embed.add_field(name="Product ID", value=f"`{p.id}`")
            embed.add_field(name="Stock", value=f"{p.stock}")
            if p.example_image:
                embed.set_image(url=p.example_image)
            if p.temp:
                embed.set_footer(
                    text="This is a limited time product. To buy it, use /buy <product id>"
                )
            else:
                embed.set_footer(text="To buy this product, use /buy <product id>")
            embeds.append(embed)
        sexy_paginator = ButtonPagination()
        await sexy_paginator.start(ctx, pages=embeds)

    @app_commands.command(name="order-cancel")
    async def _cancel(self, interaction: discord.Interaction, transaction_id: int):
        try:
            transaction = await Transactions.get(id=transaction_id)
        except:
            await interaction.response.send_message(
                "Transaction not found! Hint: transaction ids look like TXN-{user id}"
            )
            return
        if transaction.paid:
            await interaction.response.send_message("This order is already paid!")
            return
        await transaction.delete()
        await interaction.response.send_message("Order cancelled!")

    @app_commands.command(name="earnings")
    async def earnings(self, interaction: discord.Interaction):
        records = await Transactions.filter(paid=True).all()
        total = sum([r.amount for r in records])
        await interaction.response.send_message(f"Total earnings: {total}")

    @app_commands.command(name="discount")
    async def discount(self, interaction: discord.Interaction, discount: int):
        ignored = []
        async for p in Products.all():
            p.price = p.price - (p.price * (discount / 100))
            if p.price <= 0:
                ignored.append(p.name)
                continue
            await p.save()
        fmt = (
            None
            if len(ignored) == 0
            else f"\nCannot apply discount on: {', '.join(ignored)}"
        )
        await interaction.response.send_message(
            f"Discounted all products by {discount}%{fmt}"
        )

    @app_commands.command(name="product-add")
    async def add(
        self,
        interaction: discord.Interaction,
        name: str,
        price: int,
        description: str,
        role: discord.Role = None,
        actual_image: discord.Attachment = None,
        example_image: discord.Attachment = None,
        temp: bool = False,
        stock: int = 10,
        user: discord.Member = None,
    ):
        if role:
            role = role.id
        if actual_image:
            actual_image = actual_image.url
        if example_image:
            example_image = example_image.url
        if user:
            user = user.id
        await Products.create(
            name=name,
            price=price,
            description=description,
            role=role,
            image=actual_image,
            example_image=example_image,
            temp=temp,
            stock=stock,
            user=user,
        )
        await interaction.response.send_message(f"Added product {name} with 10 stocks!")

    @app_commands.command(name="product-remove")
    async def remove(self, interaction: discord.Interaction, id: int):
        await Products.filter(id=id).delete()
        await interaction.response.send_message("Removed product!")


async def setup(bot):
    await bot.add_cog(cmds(bot))
