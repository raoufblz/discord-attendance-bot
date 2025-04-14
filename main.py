"""
Main file for the Discord bot

initializes the bot, loads environment variables,
imports necessary modules, and runs the bot with the Discord token (in .env file).
"""

from dotenv import dotenv_values
import discord
from shared import bot

# Load environment variables
config = dotenv_values(".env")
TOKEN = config.get('TOKEN')

if not TOKEN:
    raise ValueError("No TOKEN found in .env file.")

# import modules after initialization (don t ever touch this)
import events
import commands
import utils

# run the bot
if __name__ == '__main__':
    """
    Runs the bot with the token from the .env file and handles
    any exceptions that might occur during startup.
    """
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Invalid Discord token. Check your .env file")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

