"""
Shared resources for the Discord bot (voice data and global start time)

this file contains shared variables and objects used across the bot,
including the bot instance, intents configuration, and global data structures
for tracking voice activity.
"""
import discord
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Dictionary inside a dictionary to store voice activity data for all members
# Format: {member_id: {"join_time": datetime, "total_duration": timedelta, "channel_name": str}}
voice_data = {}

# global variable to track when the bot started its session
global_start_time = None
