import discord, aiohttp
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from models import (
    Products,
    Transactions,
    RoleDiscounts,
    Role_Products,
    Role_Transactions,
)
from core.utils import ButtonPagination, email_input, prompt, choose_one


class cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_role_buy_timer_complete(self, timer):
        guild = self.bot.get_guild(timer.guild_id)
        if not guild:
            return
        role = guild.get_role(timer.message_id)
        if not role:
            return
        try:
            member = guild.get_member(timer.author_id) or await guild.fetch_member(timer.author_id)
        except:
            return
        try:
            await member.remove_roles(role)
            await member.send(f"Your role {role.name} has expired!")
        except:
            return

    @app_commands.command(name="buy-role")
    async def __buy(self, interaction: discord.Interaction, role: discord.Role = None):
        ctx = await self.bot.get_context(interaction)

        def check(message):
            if message.author == ctx.author and message.channel == ctx.channel:
                return True

        r = await Role_Transactions.filter(
            user_id=interaction.user.id, paid=False
        ).all()
        if r:
            await interaction.response.send_message(
                f"You already have an invoice pending, please complete that purchase here https://www.paypal.com/invoice/payerView/details/{r[0].payapl_id}"
            )
            return
        if role:
            try:
                product = await Role_Products.get(role_id=role.id)
            except:
                await interaction.response.send_message(
                    "Product not found! Use /buy-role to see all currently selling roles!"
                )
                return
            if product.stock <= 0:
                await interaction.response.send_message("This product is out of stock!")
                return
            product_price = product.price
            if product.discount > 0:
                product_price -= product_price * (product.discount / 100)
            role_discount = await RoleDiscounts.all()
            for r in role_discount:
                if r.role_id in [r.id for r in interaction.user.roles]:
                    product_price -= product_price * (r.discount / 100)
            await interaction.response.send_message(
                "Initiating purchase for this role!"
            )
            choices = [
                "1) 1 Month",
                "2) 3 Months",
                "3) 6 Months",
                "4) 12 Months",
            ]
            duration_dict = {
                "1": datetime.utcnow() + timedelta(days=30),
                "2": datetime.utcnow() + timedelta(days=90),
                "3": datetime.utcnow() + timedelta(days=180),
                "4": datetime.utcnow() + timedelta(days=365),
            }
            duration = await choose_one(ctx, choices)
            if not duration:
                await ctx.channel.send("Alright! Cancelling the order!")
                return
            duration = duration_dict[duration]

            await ctx.channel.send(
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
                    "invoice_number": f"TXN-ROLE-{interaction.user.id}",
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
                        "name": f"{product.role_name}",
                        "description": f"{product.description}",
                        "quantity": "1",
                        "unit_amount": {
                            "currency_code": "USD",
                            "value": f"{product_price}",
                        },
                        "unit_of_measure": "QUANTITY",
                    }
                ],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.paypal.com/v2/invoicing/invoices",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    },
                    json=paypal_data,
                ) as resp:
                    uid = (await resp.json())["id"]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.paypal.com/v2/invoicing/invoices/{uid}/send",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                    },
                    json={"send_to_invoicer": True},
                ) as resp:
                    print(f"Invoice sent to {email}!")
            await ctx.channel.send(
                "I've sent you an invoice on your email! Please check your email and pay the invoice, Thanks for purchasing with us!"
            )
            await Role_Transactions.create(
                iid=f"TXN-{interaction.user.id}",
                payapl_id=uid,
                user_id=interaction.user.id,
                role_id=role.id,
                amount=product_price,
                role_name=role.name,
            )
            await self.bot.timers.create(
                event=f"role_buy",
                expires=duration,
                author_id=interaction.user.id,
                guild_id=interaction.guild.id,
                message_id=role.id,
            )
            return
        embeds = []
        async for p in Role_Products.all():
            if p.stock <= 0:
                continue
            embed = discord.Embed(
                color=0x26FCFF, title=p.role_name, description=p.description
            )
            embed.add_field(name="Price", value=f"{p.price}$")
            embed.add_field(name="Stock", value=f"{p.stock}")
            if p.discount > 0:
                embed.add_field(
                    name="Discounted Price",
                    value=f"{p.price - (p.price * p.discount / 100)}$",
                )
            embed.set_footer(text="To buy this product, use /buy-role <role>")
            embeds.append(embed)
        sexy_paginator = ButtonPagination()
        await sexy_paginator.start(ctx, pages=embeds)

    @app_commands.command(name="product-role-add")
    @commands.is_owner()
    async def _add(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        price: int,
        description: str,
        stock: int = 10,
    ):
        await Role_Products.create(
            role_name=role.name,
            role_id=role.id,
            guild_id=interaction.guild.id,
            price=price,
            description=description,
            stock=stock,
        )
        await interaction.response.send_message(f"Added role {role} with 10 stocks!")

    @app_commands.command(name="product-role-remove")
    @commands.is_owner()
    async def _remove(self, interaction: discord.Interaction, role: discord.Role):
        await Role_Products.filter(role_id=role.id).delete()
        await interaction.response.send_message("Removed role!")

    @app_commands.command(name="role-discount")
    @commands.is_owner()
    async def _role_discount(
        self, interaction: discord.Interaction, role: discord.Role, discount: int
    ):
        try:
            r = await RoleDiscounts.get(role_id=role.id)
            if discount == 0:
                await r.delete()
                await interaction.response.send_message(
                    f"Discount for {role.name} removed!"
                )
                return
            r.discount = discount
            await r.save()
        except:
            await RoleDiscounts.create(role_id=role.id, discount=discount)
        await interaction.response.send_message(
            f"Discount for {role.name} set to {discount}%"
        )

    @app_commands.command(name="buy")
    async def _buy(self, interaction: discord.Interaction, product_id: int = None):
        ctx = await self.bot.get_context(interaction)

        def check(message):
            if message.author == ctx.author and message.channel == ctx.channel:
                return True

        r = await Transactions.filter(user_id=interaction.user.id, paid=False).all()
        if r:
            await interaction.response.send_message(
                f"You already have an invoice pending, please complete that purchase here https://www.paypal.com/invoice/payerView/details/{r[0].payapl_id}"
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
            product_price = product.price
            if product.discount > 0:
                product_price -= product_price * (product.discount / 100)
            role_discount = await RoleDiscounts.all()
            for r in role_discount:
                if r.role_id in [r.id for r in interaction.user.roles]:
                    product_price -= product_price * (r.discount / 100)
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
                            "value": f"{product_price}",
                        },
                        "unit_of_measure": "QUANTITY",
                    }
                ],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.paypal.com/v2/invoicing/invoices",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    },
                    json=paypal_data,
                ) as resp:
                    uid = (await resp.json())["id"]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.paypal.com/v2/invoicing/invoices/{uid}/send",
                    headers={
                        "Authorization": f"Bearer {self.bot.temp_token}",
                        "Content-Type": "application/json",
                    },
                    json={"send_to_invoicer": True},
                ) as resp:
                    print(f"Invoice sent to {email}!")
            await ctx.channel.send(
                "I've sent you an invoice on your email! Please check your email and pay the invoice, Thanks for purchasing with us!"
            )
            await Transactions.create(
                iid=f"TXN-{interaction.user.id}",
                payapl_id=uid,
                user_id=interaction.user.id,
                product_id=product.id,
                amount=product_price,
                product_name=product.name,
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
            if p.discount > 0:
                embed.add_field(
                    name="Discounted Price",
                    value=f"{p.price - (p.price * p.discount / 100)}$",
                )
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
    @commands.is_owner()
    async def _cancel(self, interaction: discord.Interaction, transaction_id: int):
        try:
            transaction = await Transactions.get(iid=transaction_id)
        except:
            await interaction.response.send_message(
                "Transaction not found! Hint: transaction ids look like TXN-{user id}"
            )
            return
        if transaction.paid:
            await interaction.response.send_message("This order is already paid!")
            return
        await transaction.delete()
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"https://api.paypal.com/v2/invoicing/invoices/{transaction.payapl_id}",
                headers={"Authorization": f"Bearer {self.bot.temp_token}"},
            ) as resp:
                print(f"Invoice cancelled for {transaction.user_id}")
        await interaction.response.send_message("Order cancelled!")

    @app_commands.command(name="earnings")
    @commands.is_owner()
    async def earnings(self, interaction: discord.Interaction):
        records = await Transactions.filter(paid=True).all()
        gfx_total = sum([r.amount for r in records])
        records = await Role_Transactions.filter(paid=True).all()
        role_total = sum([r.amount for r in records])
        await interaction.response.send_message(
            f"Total earnings: {gfx_total + role_total}$\nGFX: {gfx_total}$\nRoles: {role_total}$"
        )

    @app_commands.command(name="discount")
    @commands.is_owner()
    async def discount(
        self, interaction: discord.Interaction, discount: int, product_id: int = None
    ):
        if not product_id:
            async for p in Products.all():
                p.discount = discount
                await p.save()
            await interaction.response.send_message(
                f"Discounted all products by {discount}%"
            )
            return
        try:
            product = await Products.get(id=product_id)
        except:
            await interaction.response.send_message("Product not found!")
            return
        product.discount = discount
        await product.save()
        await interaction.response.send_message(
            f"Discounted {product.name} by {discount}%"
        )

    @app_commands.command(name="product-add")
    @commands.is_owner()
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
    @commands.is_owner()
    async def remove(self, interaction: discord.Interaction, id: int):
        await Products.filter(id=id).delete()
        await interaction.response.send_message("Removed product!")


async def setup(bot):
    await bot.add_cog(cmds(bot))
