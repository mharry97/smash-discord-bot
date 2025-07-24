# main.py
import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = discord.Bot()

@bot.event
async def on_ready():
    print("Bot is ready and online!")

# Load the cog
bot.load_extension("cogs.crossword_cog")

bot.run(TOKEN)
