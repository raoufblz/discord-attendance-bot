import discord
from discord.ext import commands
from discord import app_commands
from dotenv import dotenv_values
import datetime
from discord.ui import Button, View
import json
import asyncio


voice_data = {}
global_start_time = None  


"""
things to fix: creating a text channel (project-oculus), creating embeds (list , leave)
adding functions for nearly all things i could make into a function,
maybe making all the code oop


"""
