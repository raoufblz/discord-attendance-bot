"""
Command handlers for the Discord bot.

This file defines slash commands (Discord s preferred way of making commands) that allow users to interact with the bot,
including joining/leaving voice channels, listing voice activity data,
resetting tracked data, and displaying help information. Commands are
restricted to users with specific roles.
"""

import discord
import datetime
from discord.ext import commands
from shared import bot, voice_data, global_start_time
from utils import save_voice_data, load_voice_data, format_time, send_paginated_time_logs


@bot.slash_command(name="join", description="The bot will join the server")
@commands.has_any_role("Moderator", "Admin", "admin", "Leaders","ADMIN", "LEADER")
async def join(ctx):
    """
    Joins the voice channel that the user is in.
    
    This command makes the bot join the voice channel where the user is currently connected to,
    it initializes tracking for all members already in the channel.
    
    Parameters
    ----------
    ctx : discord.ApplicationContext
        The context of the slash command.
        
    Returns
    -------
    None
    """
    await ctx.defer()
    
    # checks if bot is already in a voice channel in this guild
    existing_vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if existing_vc and existing_vc.is_connected():
        return await ctx.respond(f"{bot.user.name} is already connected to {existing_vc.channel.name}")
    
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            voice_client = await channel.connect()
            now = datetime.datetime.now()
    
            # set global start time
            global global_start_time
            global_start_time = now
    
            # add bot to voice_data
            voice_data[bot.user.id] = {
                "join_time": now,
                "total_duration": datetime.timedelta(),
                "channel_name": channel.name
            }
    
            # Initialize voice_data for all members already in the channel
            for member in channel.members:
                if member.id != bot.user.id:
                    voice_data[member.id] = {
                        "join_time": now,
                        "total_duration": datetime.timedelta(),
                        "channel_name": channel.name
                    }
    
            print(f"Bot joined voice channel: {channel.name} at {now}")
            await ctx.respond(f"{bot.user.name} joined voice channel: {channel.name}")
        except Exception as e:
            await ctx.respond(f"Error joining voice channel: {e}")
    else:
        await ctx.respond("You are not connected to a voice channel.")
 

@bot.slash_command(name="leave", description="Leaves the voice channel and sends the time spent by each member and the bot")
@commands.has_any_role("Moderator", "Admin", "admin", "Leaders","ADMIN", "LEADER")
async def leave(ctx):
    """
    Leave the voice channel and display time tracking results.
    
    This command makes the bot leave the voice channel and displays a paginated
    list of all members' time spent in the channel, sorted by duration.
    The user must be in the same voice channel as the bot.
    
    Parameters
    ----------
    ctx : discord.ApplicationContext
        The context of the slash command.
        
    Returns
    -------
    None
    """
    await ctx.defer()
    save_voice_data()

    # retrieve the correct voice_client for the guild
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        try:
            if ctx.author.voice and ctx.author.voice.channel == voice_client.channel:
                now = datetime.datetime.now()
                members_data = []

                # update durations for members still in voice channels
                for member_id, data in voice_data.items():
                    join_time = data['join_time']
                    if join_time:
                        duration = now - join_time
                        data['total_duration'] += duration
                        data['join_time'] = None

                # sort voice_data by total_duration (descending order)
                sorted_members = sorted(
                    voice_data.items(),
                    key=lambda x: x[1]["total_duration"].total_seconds(),
                    reverse=True
                )

                for member_id, data in sorted_members:
                    member = ctx.guild.get_member(member_id)
                    member_name = member.name if member else f"Unknown member (ID: {member_id})"
                    total_duration = format_time(data['total_duration'])
                    members_data.append(f"**{member_name}** was in {data['channel_name']} for: {total_duration}")

                await send_paginated_time_logs(ctx, members_data)

                voice_data.clear()
                await voice_client.disconnect()
                await ctx.respond(f"{bot.user.name} left the voice channel.")
            else:
                await ctx.respond("You are not in the same voice channel as the bot.")
        except Exception as e:
            await ctx.respond(f"Error leaving voice channel: {e}")
    else:
        await ctx.respond("I am not connected to a voice channel.")
 
@bot.slash_command(name="list", description="Returns a numbered, sorted list of durations")
@commands.has_any_role("Moderator", "Admin", "admin", "Leaders","ADMIN", "LEADER")
async def list(ctx):
    """
    Displays a real-time list of time spent by members in the same voice channel.
    
    This command generates a paginated list of all tracked members and their
    time spent in the same voice channel, sorted by duration in descending order.
    It calculates current session durations for members still in voice channels.
    
    Parameters
    ----------
    ctx : discord.ApplicationContext
        The context of the slash command.
        
    Returns
    -------
    None
    """
    await ctx.defer()
    await ctx.respond("Generating real-time list...")
    print("list command called")
    
    # create a copy of voice_data to avoid modifying the original (do not touch this)
    temp_voice_data = {}
    now = datetime.datetime.now()
    members_data = []
    
    # update durations for members still in voice channels
    for member_id, data in voice_data.items():
        # create a copy of the member data
        temp_data = {
            "join_time": data["join_time"],
            "total_duration": datetime.timedelta(seconds=data["total_duration"].total_seconds()),
            "channel_name": data["channel_name"]
        }
        
        # calculate current session duration if member is in a voice channel
        if temp_data["join_time"]:
            current_duration = now - temp_data["join_time"]
            temp_data["total_duration"] += current_duration
        
        temp_voice_data[member_id] = temp_data
 
    # sorts temp_voice_data by total_duration (descending order)
    sorted_members = sorted(
        temp_voice_data.items(),
        key=lambda x: x[1]["total_duration"].total_seconds(),
        reverse=True
    )
 
    for member_id, data in sorted_members:
        member = ctx.guild.get_member(member_id)
        member_name = member.name if member else f"Unknown member (ID: {member_id})"
        total_duration = format_time(data["total_duration"])
        members_data.append(f"**{member_name}** was in {data['channel_name']} for: {total_duration}")
 
    await send_paginated_time_logs(ctx, members_data)
 

@bot.slash_command(name="reset_data", description="Resets all voice activity data and restarts tracking")
@commands.has_any_role("Moderator", "Admin", "admin", "Leaders","ADMIN", "LEADER")
async def reset_data(ctx):
    """
    Reset all voice activity tracking data.
    
    This command clears all stored voice activity data and restarts tracking
    for members currently in the voice channel if the bot is connected.
    
    Parameters
    ----------
    ctx : discord.ApplicationContext
        The context of the slash command.
        
    Returns
    -------
    None
    """
    await ctx.defer()
    global voice_data
    voice_data.clear()
    save_voice_data()  # save the cleared data to ensure it's persisted
 
    # check if the bot is currently in a voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        now = datetime.datetime.now()
        channel = voice_client.channel
        for member in channel.members:
            voice_data[member.id] = {
                "join_time": now,
                "total_duration": datetime.timedelta(),
                "channel_name": channel.name
            }
        await ctx.respond("Voice activity data has been reset, and tracking has restarted for members in the current voice channel.")
    else:
        await ctx.respond("Voice activity data has been reset. The bot is not currently in a voice channel, so no members are being tracked.")
 

@bot.slash_command(name="help_me", description="Well, I hope it'll help")
@commands.has_any_role("Moderator", "Admin", "admin", "Leaders","ADMIN", "LEADER")
async def help_me(ctx):
    """
    Displays help information about available commands.
    
    This command provides a brief description of all available commands
    and their functionality to help users understand how to use the bot.
    
    Parameters
    ----------
    ctx : discord.ApplicationContext
        The context of the slash command.
        
    Returns
    -------
    None
    """
    await ctx.respond("/join: Makes the bot enter the voice channel you're in.\n/leave: The bot leaves the voice channel, you need to be in the VC for it to work; it calculates the time spent by each member and logs it.\n/list: Real-time list.\n/reset_data: Resets all voice activity data and restarts tracking.")
