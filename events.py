import discord
import datetime
from shared import bot, voice_data, global_start_time
from utils import load_voice_data, save_voice_data, periodic_save, ensure_bot_channel

# bot events
@bot.event
async def on_ready():
    await bot.sync_commands()  # py-cord now
    # load data into the shared variable
    temp_data = load_voice_data()
    voice_data.clear()
    voice_data.update(temp_data)
    
    print(f'logged in as {bot.user}\n------------------------')
    
    # iterate through all guilds the bot is in
    for guild in bot.guilds:
        # find a channel with the <bot channel name> as its name
        target_channel = None
        for channel in guild.text_channels:
            if "project-oculus" in channel.name.lower():  # case-insensitive check
                target_channel = channel
                break
        
        if target_channel:
            await target_channel.send("hello!!! beep boop! if you'd like to try this bot you could add it to your server using this link: insert your bot link")
        else:
            print(f"no channel with 'project-oculus' in its name found in guild: {guild.name}")
            
    bot.loop.create_task(periodic_save())

    # create <bot channel name> in all guilds if it doesn't exist
    for guild in bot.guilds:
        await ensure_bot_channel(guild)

@bot.event
async def on_guild_join(guild):
    await ensure_bot_channel(guild) 
    
@bot.event
async def on_guild_channel_delete(channel):
    if channel.name == "project-oculus":
        guild = channel.guild
        await ensure_bot_channel(guild)
        

@bot.event
async def on_resumed():
    global voice_data
    voice_data = load_voice_data()
    print(f"{bot.user} reconnected to discord.")

    # attempt to reconnect to the last known voice channel
    for guild in bot.guilds:
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        if not voice_client:
            # find the last known channel from voice_data
            for member_id, data in voice_data.items():
                channel_name = data.get("channel_name")
                if channel_name:
                    channel = discord.utils.get(guild.voice_channels, name=channel_name)
                    if channel:
                        try:
                            await channel.connect()
                            print(f"reconnected to voice channel: {channel.name}")
                            
                            # reinitialize voice_data for all members currently in the channel
                            now = datetime.datetime.now()
                            for member in channel.members:
                                if member.id not in voice_data:
                                    voice_data[member.id] = {
                                        "join_time": now,
                                        "total_duration": datetime.timedelta(),
                                        "channel_name": channel.name
                                    }
                                else:
                                    voice_data[member.id]["join_time"] = now
                                    voice_data[member.id]["channel_name"] = channel.name
                            break
                        except Exception as e:
                            print(f"failed to reconnect to voice channel {channel.name}: {e}")

@bot.event
async def on_disconnect():
    now = datetime.datetime.now()
    for member_id, data in voice_data.items():
        if data["join_time"]:
            data["total_duration"] += now - data["join_time"]
            data["join_time"] = None
    save_voice_data()
    print(f"{bot.user} disconnected from discord.")
    
    # clean up voice clients
    for vc in bot.voice_clients:
        try:
            await vc.disconnect(force=True)
        except Exception as e:
            print(f"error disconnecting from voice channel: {e}")

    # iterate through all guilds the bot is in
    for guild in bot.guilds:
        # find a channel with <bot channel name> as its name
        target_channel = None
        for channel in guild.text_channels:
            if "project-oculus" in channel.name.lower():  # case-insensitive check
                target_channel = channel
                break
        
        if target_channel:
            await target_channel.send("error detected! system malfunction! the internet!!! beep beep initiating shutdown... or maybe just rebooting... the end is neaaaarr!!")
        else:
            print(f"no channel with 'project-oculus' in its name found in guild: {guild.name}")
            

# handle voice state updates
@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.datetime.now()

    # check if the bot is connected to a voice channel
    if not bot.voice_clients:
        return

    # find the bot's voice client in the member's guild
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if not voice_client:
        return  # bot is not in a voice channel in this guild
    
    bot_channel = voice_client.channel

    # member joined the bot's channel
    if after.channel and after.channel.id == bot_channel.id and before.channel != after.channel:
        # initialize or update member's data
        if member.id not in voice_data:
            voice_data[member.id] = {
                "join_time": now,
                "total_duration": datetime.timedelta(),
                "channel_name": after.channel.name
            }
        else:
            voice_data[member.id]["join_time"] = now
            voice_data[member.id]["channel_name"] = after.channel.name
        print(f"{member.name} joined {after.channel.name} at {now}")
    
    # member left the bot's channel
    elif before.channel and before.channel.id == bot_channel.id and before.channel != after.channel:
        if member.id in voice_data and voice_data[member.id]["join_time"]:
            duration = now - voice_data[member.id]["join_time"]
            voice_data[member.id]["total_duration"] += duration
            voice_data[member.id]["join_time"] = None
            print(f"{member.name} left {before.channel.name} after {duration}")
    
    # handle bot movement
    if member.id == bot.user.id:
        if before.channel != after.channel:
            # bot left a channel, update all members in that channel
            if before.channel:
                for member_id, data in voice_data.items():
                    if data["join_time"] and member_id != bot.user.id:
                        member_obj = before.channel.guild.get_member(member_id)
                        if member_obj and member_obj.voice and member_obj.voice.channel == before.channel:
                            duration = now - data["join_time"]
                            data["total_duration"] += duration
                            data["join_time"] = None
                            print(f"Updated {member_obj.name}'s time: +{duration}")

            # bot joined a channel, start tracking all members already in the channel
            if after.channel:
                for member in after.channel.members:
                    if member.id != bot.user.id:
                        if member.id not in voice_data:
                            voice_data[member.id] = {
                                "join_time": now,
                                "total_duration": datetime.timedelta(),
                                "channel_name": after.channel.name
                            }
                        else:
                            voice_data[member.id]["join_time"] = now
                            voice_data[member.id]["channel_name"] = after.channel.name
                        print(f"Started tracking {member.name} in {after.channel.name}")
