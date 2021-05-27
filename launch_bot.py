import os
import sys
from dotenv import load_dotenv

from discord.ext.commands import Bot

from src.azuria_bot import AzuriaBot


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '!'

AUTHOR = 'AzuriaCristal'

bot = Bot(command_prefix=PREFIX)
bot.add_cog(AzuriaBot(bot, author=AUTHOR, n=2))
bot.run(TOKEN)
