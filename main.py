import discord, asyncio, core.config as config
from discord import AllowedMentions, Activity, ActivityType
from core.bot import ppbot

#TODO: /off command with % with specific role | temprole with paypal

intents = discord.Intents.default()
intents.message_content = True

botwa = ppbot(
    command_prefix="$",
    owner_ids=config.owners,
    intents=intents,
    case_insensitive=True,
    allowed_mentions=AllowedMentions(
        everyone=False, roles=False, replied_user=False, users=True
    ),
    activity=Activity(type=ActivityType.listening, name=f"hello world!"),
)

async def main():
    async with botwa:
        await botwa.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
