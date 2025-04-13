import discord
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)
voice_data = {}
global_start_time = None
