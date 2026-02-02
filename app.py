import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import aiohttp
from aiohttp import web

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = "http://bio.thug4ff.com/update_bio"
KEY = "great"
PORT = int(os.getenv("PORT", 5000))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

session = None
cooldowns = {}

REGIONS = {
    "ID": ("Indonesia", "🇮🇩"),
    "TH": ("Thailand", "🇹🇭"),
    "IND": ("India", "🇮🇳"),
    "BR": ("Brazil", "🇧🇷"),
    "SG": ("Singapore", "🇸🇬"),
    "BD": ("Bangladesh", "🇧🇩"),
    "PK": ("Pakistan", "🇵🇰"),
    "US": ("United States", "🇺🇸"),
    "MY": ("Malaysia", "🇲🇾"),
    "VN": ("Vietnam", "🇻🇳"),
    "EUROPE": ("Europe", "🇪🇺"),
    "RU": ("Russia", "🇷🇺"),
}

def format_region(code: str):
    code = code.upper()
    if code in REGIONS:
        name, flag = REGIONS[code]
        return f"{flag} {name}"
    return code

@bot.event
async def on_ready():
    global session
    if session is None:
        session = aiohttp.ClientSession()
    print(f"Logged in as {bot.user}")

@bot.command(name="bio")
async def bio(ctx, access_token: str = None, *, bio: str = None):
    if not access_token or not bio:
        return await ctx.reply(
            "**Usage:**\n`!bio <access_token> <new bio>`\n\n"
            "**Example:**\n`!bio ABC123 Hello world!`"
        )

    now = datetime.now().timestamp()
    last = cooldowns.get(ctx.author.id, 0)
    if now - last < 30:
        return await ctx.send(
            f"⏳ Please wait **{int(30 - (now - last))}s** before reusing this command.",
            delete_after=6
        )
    cooldowns[ctx.author.id] = now

    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send("⏳ Updating bio just wait a moment...", delete_after=3)

    url = f"{API_URL}?access_token={access_token}&bio={bio}&key={KEY}"

    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ API error.", delete_after=6)
            data = await resp.json()

        if data.get("status") == "error":
            return await ctx.send("❌ Invalid or expired token.", delete_after=6)

        region = format_region(data.get("region", "UNK"))

        embed = discord.Embed(
            title="✅ Bio Updated !",
            color=0x77d5a3,
            description=(
                f"> **Nickname:** {data.get('nickname', 'Unknown')}\n"
                f"> **Platform:** {data.get('platform', 'Unknown')}\n"
                f"> **Region:** {region}\n"
                f"> **UID:** {data.get('uid', 'Unknown')}\n"
                f"> **New Bio:** ||{data.get('bio', '')}||"
            )
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="DEVELOPED BY Benzz")
        await ctx.send(ctx.author.mention, embed=embed)

    except Exception as e:
        print(e)
        await ctx.send("❌ Unexpected error.", delete_after=6)

async def start_web_server():
    app = web.Application()
    async def handle(request):
        return web.Response(text="Bot is running ✅")
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Web server running on port {PORT}")

async def main():
    await start_web_server()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
