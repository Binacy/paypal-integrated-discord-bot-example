import typing, discord, itertools, asyncio
from typing import Optional, NamedTuple
from discord.ext import commands
from discord import (
    Embed,
    Interaction,
    ui,
    ButtonStyle,
    Color,
    Message,
)

class choose(ui.View):
    def __init__(
        self, *, timeout: float, author_id: list, ctx, delete_after: bool
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[str] = None
        self.delete_after: bool = delete_after
        self.author_id: list = author_id
        self.ctx = ctx
        self.message: Optional[Message] = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user and interaction.user.id in self.author_id:
            return True
        await interaction.response.send_message(
            "This is not for you dummy.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        try:
            if self.message:
                return await self.message.delete()
        except:
            return

    @ui.button(style=ButtonStyle.grey, emoji='1️⃣')
    async def one(self, interaction, button):
        self.value = '1'
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()

    @ui.button(style=ButtonStyle.grey, emoji='2️⃣')
    async def two(self, interaction, button):
        self.value = '2'
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()

    @ui.button(style=ButtonStyle.grey, emoji='3️⃣')
    async def three(self, interaction, button):
        self.value = '3'
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()

    @ui.button(style=ButtonStyle.grey, emoji='4️⃣')
    async def four(self, interaction, button):
        self.value = '4'
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()

    @ui.button(style=ButtonStyle.grey, emoji="⏹️")
    async def stawppp(self, interaction, button):
        await interaction.response.defer()
        await interaction.message.delete()
        self.stop()

async def choose_one(ctx, choices):
    authors = [ctx.author.id]
    for i in ctx.bot.owner_ids:
        authors.append(i)
    view = choose(timeout=30, delete_after=False, ctx=ctx, author_id=authors)
    embed = Embed(
        description=(
            "Please choose your time duration for buying this role:\n\n"
            + "\n".join(choices)
        ),
        color=0x26fcff,
    )
    embed.set_author(
        name=f"{ctx.author}",
        icon_url=ctx.author.avatar.url
    )

    view.message = await ctx.channel.send(content=None, embed=embed, view=view)
    await view.wait()
    if view.value is None:
        return None
    return choices[view.value]

async def email_input(ctx, check, timeout=60):
    try:
        message = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return await ctx.send("Took too long. Good Bye.")
    else:
        await message.delete()
        return message.content


class ButtonPagination(ui.View):
    def __init__(
        self,
        *,
        timeout: int = 60,
        PageCounterStyle: ButtonStyle = ButtonStyle.grey,
        InitialPage: int = 0,
    ) -> None:
        self.PageCounterStyle = PageCounterStyle
        self.InitialPage = InitialPage

        self.pages = None
        self.ctx = None
        self.bot = None
        self.message = None
        self.current_page = None
        self.total_page_count = None

        super().__init__(timeout=timeout)

    async def on_timeout(self):
        try:
            for i in self.children:
                i.disabled = True
            return await self.message.edit(view=self)
        except:
            ...

    async def start(self, ctx: commands.Context, pages: list):
        self.pages = pages
        self.total_page_count = len(pages)
        self.ctx = ctx
        self.bot = ctx.bot
        self.current_page = self.InitialPage
        self.alloweds = [self.ctx.author.id]
        for i in self.ctx.bot.owner_ids:
            self.alloweds.append(i)
        FirstButton: ui.Button = ui.Button(emoji="⏮️")
        LastButton: ui.Button = ui.Button(emoji="⏭️")
        StopButton: ui.Button = ui.Button(emoji="⏹️")
        PreviousButton: ui.Button = ui.Button(emoji="◀️")
        NextButton: ui.Button = ui.Button(emoji="▶️")

        StopButton.callback = self.stop_button_callback
        LastButton.callback = self.last_button_callback
        FirstButton.callback = self.first_button_callback
        PreviousButton.callback = self.previous_button_callback
        NextButton.callback = self.next_button_callback
        self.add_item(FirstButton)
        self.add_item(PreviousButton)
        self.add_item(StopButton)
        self.add_item(NextButton)
        self.add_item(LastButton)
        self.message = await ctx.send(embed=self.pages[self.InitialPage], view=self)

    async def first(self):
        self.current_page = 0

        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def previous(self):
        if self.current_page == 0:
            self.current_page = self.total_page_count - 1
        else:
            self.current_page -= 1

        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def stop(self):
        self.current_page = 0
        try:
            await self.message.delete()
        except:
            return

    async def next(self):
        if self.current_page == self.total_page_count - 1:
            self.current_page = 0
        else:
            self.current_page += 1

        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def last(self):
        self.current_page = self.total_page_count - 1

        await self.message.edit(embed=self.pages[self.current_page], view=self)

    async def last_button_callback(self, interaction: Interaction):
        if interaction.user.id not in self.alloweds:
            embed = Embed(
                description="You cannot control this pagination.", color=Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()
        await self.last()

    async def first_button_callback(self, interaction: Interaction):
        if interaction.user.id not in self.alloweds:
            embed = Embed(
                description="You cannot control this pagination.", color=Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()
        await self.first()

    async def stop_button_callback(self, interaction: Interaction):
        if interaction.user.id not in self.alloweds:
            embed = Embed(
                description="You cannot control this pagination.", color=Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()
        await self.stop()

    async def next_button_callback(self, interaction: Interaction):
        if interaction.user.id not in self.alloweds:
            embed = Embed(
                description="You cannot control this pagination.", color=Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()
        await self.next()

    async def previous_button_callback(self, interaction: Interaction):
        if interaction.user.id not in self.alloweds:
            embed = Embed(
                description="You cannot control this pagination.", color=Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.response.defer()
        await self.previous()


class Page(NamedTuple):
    index: int
    content: str


def get_chunks(iterable, size):
    it = iter(iterable)
    return iter(lambda: tuple(itertools.islice(it, size)), ())


async def paginate(ctx, entries, title=None, per_page=10):
    abc = Pages(ctx, title=title, entries=entries, per_page=per_page)
    await abc.paginate()


class PagesBase:
    def __init__(self, pages: list):
        self.pages = pages
        self.cur_page = 1

    @property
    def current_page(self) -> Page:
        return Page(self.cur_page, self.pages[self.cur_page - 1])

    @property
    def next_page(self):
        if self.cur_page == self.total:
            return None

        self.cur_page += 1
        return self.current_page

    @property
    def previous_page(self):
        if self.cur_page == 1:
            return None

        self.cur_page -= 1
        return self.current_page

    @property
    def first_page(self) -> Page:
        self.cur_page = 1
        return self.current_page

    @property
    def last_page(self) -> Page:
        self.cur_page = self.total
        return self.current_page

    @property
    def total(self):
        return len(self.pages)


class Pages:
    def __init__(
        self,
        ctx,
        *,
        entries,
        per_page=10,
        footericon=None,
        footertext=None,
        thumbnail=None,
        timeout=60.0,
        title=None,
        show_page_count=True,
    ):
        self.ctx = ctx
        self.bot = ctx.bot
        self.per_page = per_page
        self.timeout = timeout
        self.title = title
        self.thumbnail = thumbnail
        self.footericon = footericon
        self.footertext = footertext
        self.show_page_count = show_page_count

        self.lines = entries
        self.pages = None

    @property
    def embed(self):
        page = self.pages.current_page

        e = Embed(color=self.bot.color)
        if self.title:
            e.title = self.title

        if self.footertext and not self.footericon:
            e.set_footer(text=self.footertext)
        if self.footericon and self.footertext:
            e.set_footer(text=self.footertext, icon_url=self.footericon)
        if not self.footericon and not self.footertext and self.show_page_count is True:
            e.set_footer(
                text=f"{self.ctx.me.name} • Page {page.index}/{self.pages.total}",
                icon_url=self.ctx.me.avatar.url,
            )
        if self.thumbnail:
            e.set_thumbnail(url=self.thumbnail)
        e.description = page.content

        return e

    async def paginate(self):
        _pages = []
        for page in get_chunks(self.lines, self.per_page):
            _pages.append("".join(page))

        self.pages = PagesBase(_pages)

        if not self.pages.total > 1:
            return await self.ctx.send(embed=self.embed)
        view = PaginatorView(
            self.ctx,
            pages=self.pages,
            embed=self.embed,
            timeout=self.timeout,
            show_page_count=self.show_page_count,
            title=self.title,
            thumbnail=self.thumbnail,
            footertext=self.footertext,
        )
        view.message = await self.ctx.send(embed=self.embed, view=view)


class PaginatorView(ui.View):
    def __init__(
        self,
        ctx,
        pages: PagesBase,
        embed,
        timeout,
        show_page_count,
        title=None,
        thumbnail=None,
        footertext=None,
    ):
        super().__init__(timeout=timeout)

        self.ctx = ctx
        self.bot = ctx.bot
        self.pages = pages
        self.embed = embed
        self.title = title
        self.thumbnail = thumbnail
        self.footertext = footertext
        self.show_page_count = show_page_count

        if self.pages.cur_page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

    def update_embed(self, page: Page):
        if self.title:
            self.embed.title = self.title
        if self.thumbnail:
            self.embed.set_thumbnail(url=self.thumbnail)
        if self.footertext:
            self.embed.set_footer(text=self.footertext)
        elif self.show_page_count:
            self.embed.set_footer(
                text=f"{self.ctx.me.name} • Page {page.index}/{self.pages.total}",
                icon_url=self.ctx.me.avatar.url,
            )

        self.embed.description = page.content

    def lock_bro(self):
        if self.pages.cur_page == self.pages.total:
            self.children[0].disabled = False
            self.children[1].disabled = False

            self.children[3].disabled = True
            self.children[4].disabled = True

        elif self.pages.cur_page == 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

            self.children[3].disabled = False
            self.children[4].disabled = False

        elif 1 < self.pages.cur_page < self.pages.total:
            for b in self.children:
                b.disabled = False

    async def interaction_check(self, interaction: Interaction) -> bool:
        alloweds = [self.ctx.author.id]
        for i in self.bot.owner_ids:
            alloweds.append(i)
        if interaction.user.id not in alloweds:
            await interaction.response.send_message(
                "You cannot control this pagination.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        try:
            for b in self.children:
                b.style, b.disabled = ButtonStyle.grey, True

            await self.message.edit(view=self)
        except:
            ...

    @ui.button(style=ButtonStyle.grey, emoji="⏮️")
    async def first(self, interaction, button):
        page = self.pages.first_page
        await interaction.response.defer()

        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @ui.button(style=ButtonStyle.grey, emoji="◀️")
    async def previous(self, interaction, button):
        page = self.pages.previous_page
        await interaction.response.defer()
        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @ui.button(style=ButtonStyle.grey, emoji="⏹️")
    async def stop(self, interaction, button):
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except:
            ...

    @ui.button(style=ButtonStyle.grey, emoji="▶️")
    async def next(self, interaction, button):
        page = self.pages.next_page
        await interaction.response.defer()
        self.update_embed(page)

        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)

    @ui.button(style=ButtonStyle.grey, emoji="⏭️")
    async def last(self, interaction, button):
        page = self.pages.last_page
        await interaction.response.defer()

        self.update_embed(page)
        self.lock_bro()
        await interaction.message.edit(embed=self.embed, view=self)


class ConfirmationView(discord.ui.View):
    def __init__(
        self, *, timeout: float, author_id: int, ctx, delete_after: bool
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: typing.Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.ctx = ctx
        self.message: typing.Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        await interaction.response.send_message(
            "This confirmation is not for you.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        try:
            if self.delete_after and self.message:
                return await self.message.delete()
        except:
            return

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction, button):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction, button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.message.delete()
        self.stop()


async def prompt(
    ctx,
    message,
    timeout=30.0,
    delete_after=True,
    author_id=None,
):
    """
    An interactive reaction confirmation dialog.
    """

    author_id = author_id or ctx.author.id
    view = ConfirmationView(
        timeout=timeout,
        delete_after=delete_after,
        ctx=ctx,
        author_id=author_id,
    )
    embed = discord.Embed(description=f"**{message}**", color=0x26FCFF)
    view.message = await ctx.send(embed=embed, view=view)
    await view.wait()
    return view.value
