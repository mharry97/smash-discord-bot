# main.py
import os
import discord
from dotenv import load_dotenv
import database as db

load_dotenv()
TOKEN = os.getenv('TOKEN')
# Run the database setup function once on startup
db.setup_database()

bot = discord.Bot(intents=discord.Intents.default())

@bot.event
async def on_ready():
    print("Bot is ready and online!")

# Load the cogs
bot.load_extension("cogs.crossword.crossword_cog")
bot.load_extension("cogs.misc.misc_cog")

bot.run(TOKEN)
