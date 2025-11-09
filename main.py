import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import instaloader
import re
from aiohttp import web

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
L = instaloader.Instaloader()

# Custom download path (from env or default)
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', '/usr/app/downloads/ig')

# Pyrogram client setup
API_ID = int(os.getenv('API_ID'))  # Your API ID
API_HASH = os.getenv('API_HASH')  # Your API Hash
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Your Bot Token

app = Client("instagram_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to extract shortcode from Instagram URL
def extract_shortcode(url):
    match = re.search(r'/p/([a-zA-Z0-9_-]+)', url) or re.search(r'/reel/([a-zA-Z0-9_-]+)', url) or re.search(r'/stories/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

# Function to download media
def download_media(shortcode):
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=DOWNLOAD_DIR)
        # Find the downloaded file
        for file in os.listdir(DOWNLOAD_DIR):
            if file.endswith(('.mp4', '.jpg', '.png')):
                return os.path.join(DOWNLOAD_DIR, file)
    except Exception as e:
        logger.error(f"Download failed: {e}")
    return None

# Start command
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply("Send me a public Instagram reel, post, or story URL, and I'll download and send it to you in PM!")

# Handle messages (Instagram URLs)
@app.on_message(filters.text & ~filters.command)
async def handle_message(client: Client, message: Message):
    url = message.text
    shortcode = extract_shortcode(url)
    if not shortcode:
        await message.reply("Invalid Instagram URL. Please send a public reel, post, or story link.")
        return

    await message.reply("Downloading... Please wait.")
    
    file_path = download_media(shortcode)
    if file_path:
        user_id = message.from_user.id
        with open(file_path, 'rb') as file:
            if file_path.endswith('.mp4'):
                await client.send_video(chat_id=user_id, video=file, caption="Here's your download!")
            else:
                await client.send_photo(chat_id=user_id, photo=file, caption="Here's your download!")
        
        # Clean up: Delete the file
        os.remove(file_path)
        # Clean up the downloads folder
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))
    else:
        await message.reply("Failed to download. Ensure the content is public and the URL is correct.")

# Aiohttp health check app
async def health_check(request):
    return web.Response(text="OK", status=200)

async def run_web_server():
    web_app = web.Application()
    web_app.router.add_get('/health', health_check)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health check server started on port 8080")

async def main():
    # Ensure download directory exists
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Start web server for health checks
    asyncio.create_task(run_web_server())
    
    # Start Pyrogram bot
    await app.start()
    logger.info("Bot started")
    await app.idle()  # Keep running

if __name__ == '__main__':
    asyncio.run(main())
