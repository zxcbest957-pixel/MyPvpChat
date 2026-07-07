import os
import sys
import asyncio
from datetime import datetime
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import aiohttp
from aiohttp import web

# Force UTF-8 encoding for stdout/stderr to prevent character encoding issues on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# Load configurations
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("CHANNEL_ID")
SEND_INTERVAL_MINUTES_STR = os.getenv("SEND_INTERVAL_MINUTES", "65")

# Validation
if not TOKEN or TOKEN.strip() == "":
    print("[ERROR] DISCORD_TOKEN is missing in the .env file.")
    sys.exit(1)

if not CHANNEL_ID_STR or not CHANNEL_ID_STR.strip().isdigit():
    print("[ERROR] CHANNEL_ID must be a valid numeric channel ID in the .env file.")
    sys.exit(1)

CHANNEL_ID = int(CHANNEL_ID_STR)

try:
    SEND_INTERVAL_MINUTES = int(SEND_INTERVAL_MINUTES_STR)
except ValueError:
    SEND_INTERVAL_MINUTES = 65

AD_MESSAGE = (
    "╭━━━【 MyPvP 】Clan — Maxed Out ━━━╮\n"
    "┃ ⚡ | Clan Lvl: 10 | BP: 50 | Shop: 4\n"
    "┃ 🏆 | Recruiting: Gold+ or 1500+ Wins\n"
    "┃ 🌍 |  Global community, active daily\n"
    "┃ 📥 | DM <@1522368164829331658> to apply!\n"
    "╰─────────────────────────────────╯"
)

# Client initialization (Self-bot)
client = discord.Client(self_bot=True)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Web Server handler
async def web_handle(request):
    return web.Response(text=f"Bot is running! Last check: {get_timestamp()}")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', web_handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render binds the port dynamically via $PORT
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"[{get_timestamp()}] [WEB] Web server started on port {port}")

# Self-pinging loop to keep Render service awake
@tasks.loop(minutes=10)
async def self_ping_loop():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(render_url) as response:
                    print(f"[{get_timestamp()}] [SELF-PING] Pinged {render_url} successfully. Status: {response.status}")
        except Exception as e:
            print(f"[{get_timestamp()}] [SELF-PING ERROR] Failed to ping {render_url}: {e}")

@client.event
async def on_ready():
    print("=" * 60)
    print(f"Logged in as USER: {client.user.name} (ID: {client.user.id})")
    print(f"Target Channel ID: {CHANNEL_ID}")
    print(f"Interval: {SEND_INTERVAL_MINUTES} minutes")
    print("=" * 60)
    
    # Start the loops if not already running
    if not send_ad_loop.is_running():
        send_ad_loop.start()
    if not self_ping_loop.is_running():
        self_ping_loop.start()

@tasks.loop(minutes=SEND_INTERVAL_MINUTES)
async def send_ad_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        try:
            channel = await client.fetch_channel(CHANNEL_ID)
        except Exception as e:
            print(f"[{get_timestamp()}] [ERROR] Could not find or fetch channel {CHANNEL_ID}: {e}")
            return
            
    if channel:
        try:
            print(f"[{get_timestamp()}] Sending advertisement message...")
            # Simulate human typing before sending to look more natural (3 seconds)
            async with channel.typing():
                await asyncio.sleep(3)
            
            await channel.send(AD_MESSAGE)
            print(f"[{get_timestamp()}] [SUCCESS] Advertisement sent to #{channel.name} (ID: {channel.id})")
        except Exception as e:
            print(f"[{get_timestamp()}] [ERROR] Failed to send advertisement: {e}")
    else:
        print(f"[{get_timestamp()}] [ERROR] Channel with ID {CHANNEL_ID} was not found or is inaccessible.")

async def main():
    # Start the local web server
    await start_web_server()
    # Start the discord client
    try:
        await client.start(TOKEN)
    except discord.errors.LoginFailure:
        print("[ERROR] Login failed. The DISCORD_TOKEN provided in .env is invalid.")
        sys.exit(1)
    except Exception as e:
        print(f"[CRITICAL ERROR] Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting Discord Advertisement Self-bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down bot...")
