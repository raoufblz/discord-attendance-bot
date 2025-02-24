"""
discord bot made by _raouf_blz_ *still under development (maybe??)*
    - returns a pagination with a numbered, sorted list of members who were in a 
    voice-channel, how much time each of them spent and how many they were.
    - creates a text channel to log the pagination to, even if deleted it recreates it.
    - /join: makes the bot enter the voice channel you re in and start tracking from that join_time.
    - /leave: the bot leaves the voice channel, you need to be in the vc for it to work,
    it calculates the time spent by each member and logs it.
    - the commands have role-based access.
    - saves data in case of connection problems, deletes all previous data only if /leave
    is executed.
    - /reset_data: clears all tracking data and restarts tracking.
    - /list: displays real-time tracking data in a paginated embed.
    - /help_me: lists available commands.
"""

import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import dotenv_values
import datetime
from discord.ui import Button, View
import json
import asyncio

# Load environment variables
config = dotenv_values(".env")

if 'TOKEN' not in config:
    raise ValueError("No TOKEN found in .env file.")

TOKEN = config['TOKEN']

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# Initialize bot
bot = commands.Bot(command_prefix='/', intents=intents)
voice_data = {}  # Tracks time for all members, including the bot
global_start_time = None  # Global reference timestamp

# Save voice data to a JSON file
def save_voice_data():
    try:
        with open("voice_data.json", "w") as f:
            json.dump(
                {str(k): {
                    "join_time": v["join_time"].isoformat() if v["join_time"] else None,
                    "total_duration": str(v["total_duration"].total_seconds()),
                    "channel_name": v["channel_name"]
                } for k, v in voice_data.items()},
                f
            )
        print("Voice data saved.")
    except Exception as e:
        print(f"Error saving voice data: {e}")

# Load voice data from a JSON file
def load_voice_data():
    try:
        with open("voice_data.json", "r") as f:
            data = json.load(f)
        return {
            int(k): {
                "join_time": datetime.datetime.fromisoformat(v["join_time"]) if v["join_time"] else None,
                "total_duration": datetime.timedelta(seconds=float(v["total_duration"])),
                "channel_name": v["channel_name"]
            } for k, v in data.items()
        }
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading voice data: {e}")
        return {}


# Bot events
@bot.event
async def on_ready():
    await bot.tree.sync()
    global voice_data
    voice_data = load_voice_data()
    print(f'Logged in as {bot.user}\n------------------------')
    
    # Iterate through all guilds the bot is in
    for guild in bot.guilds:
        # Find a channel with 'general' in its name
        target_channel = None
        for channel in guild.text_channels:
            if "general" in channel.name.lower():  # Case-insensitive check
                target_channel = channel
                break
        
        if target_channel:
            await target_channel.send("hello!!! Beep boop! if you'd like to try this bot you could add it to your server using this link: https://discord.com/oauth2/authorize?client_id=1337842155322085508&permissions=1385127045200&integration_type=0&scope=bot")
        else:
            print(f"No channel with 'general' in its name found in guild: {guild.name}")
            
    # Start periodic save task
    bot.loop.create_task(periodic_save())

    for guild in bot.guilds:
        # check if the attendance channel exists
        attendance_channel = discord.utils.get(guild.text_channels, name="oculus-attendance")
        if not attendance_channel:
            try:
                # creates the attendance channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(send_messages=False),
                    guild.me: discord.PermissionOverwrite(send_messages=True)
                }
                attendance_channel = await guild.create_text_channel("oculus-attendance", overwrites=overwrites)
                await attendance_channel.send("This channel logs the time spent by members in voice chats.")
                print(f"Created 'attendance' channel in guild: {guild.name}")
            except Exception as e:
                print(f"Error creating attendance channel in guild {guild.name}: {e}")


@bot.event
async def on_guild_join(guild):
    # Check if the attendance channel already exists
    attendance_channel = discord.utils.get(guild.text_channels, name="oculus-attendance")
    if not attendance_channel:
        try:
            # Create the attendance channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            attendance_channel = await guild.create_text_channel("oculus-attendance", overwrites=overwrites)
            await attendance_channel.send("This channel logs the time spent by members in voice chats, it can't be deleted forever")
        except Exception as e:
            print(f"Error creating attendance channel: {e}")


@bot.event
async def on_guild_channel_delete(channel):
    # checks if the deleted channel was the "attendance" channel
    if channel.name == "oculus-attendance":
        guild = channel.guild
        try:
            # create the attendance channel again
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            new_attendance_channel = await guild.create_text_channel("oculus-attendance", overwrites=overwrites)
            await new_attendance_channel.send("This channel logs the time spent by members in voice chats.")
        except Exception as e:
            print(f"Error recreating attendance channel: {e}")


@bot.event
async def on_resumed():
    global voice_data
    voice_data = load_voice_data()  # Reload voice data from the JSON file
    print(f"{bot.user} reconnected to Discord.")

    # Attempt to reconnect to the last known voice channel
    for guild in bot.guilds:
        voice_client = discord.utils.get(bot.voice_clients, guild=guild)
        if not voice_client:
            # Find the last known channel from voice_data
            for member_id, data in voice_data.items():
                channel_name = data.get("channel_name")
                if channel_name:
                    channel = discord.utils.get(guild.voice_channels, name=channel_name)
                    if channel:
                        try:
                            # Reconnect to the channel
                            await channel.connect()
                            print(f"Reconnected to voice channel: {channel.name}")
                            
                            # Reinitialize voice_data for all members currently in the channel
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
                            print(f"Failed to reconnect to voice channel {channel.name}: {e}")

@bot.event
async def on_disconnect():
    now = datetime.datetime.now()
    for member_id, data in voice_data.items():
        if data["join_time"]:
            data["total_duration"] += now - data["join_time"]
            data["join_time"] = None
    save_voice_data()
    print(f"{bot.user} disconnected from Discord.")
    
    # Clean up voice clients
    for vc in bot.voice_clients:
        try:
            await vc.disconnect(force=True)
        except Exception as e:
            print(f"Error disconnecting from voice channel: {e}")

    # Iterate through all guilds the bot is in
    for guild in bot.guilds:
        # Find a channel with 'general' in its name
        target_channel = None
        for channel in guild.text_channels:
            if "general" in channel.name.lower():  # Case-insensitive check
                target_channel = channel
                break
        
        if target_channel:
            await target_channel.send("Error detected! System malfunction! The internet!!! beep beep Initiating shutdown... or maybe just rebooting... THE END IS NEAAAARR!!")
        else:
            print(f"No channel with 'general' in its name found in guild: {guild.name}")
            
    
# Periodically save voice data
async def periodic_save():
    await bot.wait_until_ready()
    while not bot.is_closed():
        save_voice_data()
        print("Voice data saved (periodic save)")
        await asyncio.sleep(30)  # Save every 30 seconds (adjust as needed)

# Command to make the bot join a voice channel
@bot.hybrid_command(name="join", description="The bot will join the server")
@commands.has_any_role("Moderator", "Admin")
async def join(ctx):
    await ctx.defer()
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if voice_client:
                if voice_client.is_connected():
                    await voice_client.move_to(channel)  # Move to the new channel if already connected
                    await ctx.send(f"{bot.user.name} moved to voice channel: {channel.name}")
                    return

            # Connect to the channel if not already connected
            voice_client = await channel.connect()
            now = datetime.datetime.now()

            # Set global start time
            global global_start_time
            global_start_time = now

            # Add bot to voice_data
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
            await ctx.send(f"{bot.user.name} joined voice channel: {channel.name}")
        except Exception as e:
            await ctx.send(f"Error joining voice channel: {e}")
    else:
        await ctx.send("You are not connected to a voice channel.")

# Handle voice state updates
@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.datetime.now()

    # Check if the bot is connected to a voice channel
    if not bot.voice_clients:
        return  # Exit early if the bot is not in any voice channel

    bot_channel = bot.voice_clients[0].channel  # Get the bot's current voice channel

    # Check if the member is the bot itself
    if member.id == bot.user.id:
        if before.channel != after.channel:
            # Bot left a channel
            if before.channel:
                if member.id in voice_data and voice_data[member.id]["join_time"]:
                    duration = now - voice_data[member.id]["join_time"]
                    voice_data[member.id]["total_duration"] += duration
                    voice_data[member.id]["join_time"] = None

            # Bot joined a channel
            if after.channel:
                if member.id not in voice_data:
                    voice_data[member.id] = {
                        "join_time": now,
                        "total_duration": datetime.timedelta(),
                        "channel_name": after.channel.name
                    }
                else:
                    voice_data[member.id]["join_time"] = now
                    voice_data[member.id]["channel_name"] = after.channel.name
    else:
        # Handle other members
        if before.channel != after.channel:
            # Member left the bot's channel
            if before.channel == bot_channel:
                if member.id in voice_data and voice_data[member.id]["join_time"]:
                    duration = now - voice_data[member.id]["join_time"]
                    voice_data[member.id]["total_duration"] += duration
                    voice_data[member.id]["join_time"] = None

            # Member joined the bot's channel
            if after.channel == bot_channel:
                if member.id not in voice_data:
                    voice_data[member.id] = {
                        "join_time": now,
                        "total_duration": datetime.timedelta(),
                        "channel_name": after.channel.name
                    }
                else:
                    voice_data[member.id]["join_time"] = now
                    voice_data[member.id]["channel_name"] = after.channel.name

# Format time for display
def format_time(input_time):
    try:
        hours, minutes, seconds = map(float, input_time.split(":"))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return f"{int(total_seconds // 3600)} hr(s) {int((total_seconds % 3600) // 60)} min(s) {total_seconds % 60:.2f} sec(s)"
    except Exception as e:
        print(f"Error formatting time: {e}")
        return "Invalid time format"

# Paginator class for paginated embeds
class Paginator(View):
    def __init__(self, pages):
        super().__init__(timeout=None)  # No timeout
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction):
        """Update the message with the current page."""
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page == len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)

# Command to make the bot leave the voice channel and log durations
@bot.hybrid_command(name="leave", description="Leaves the voice channel and sends the time spent by each member and the bot")
@commands.has_any_role("Moderator", "Admin")
async def leave(ctx):
    await ctx.defer()
    save_voice_data()

    # Retrieve the correct voice_client for the guild
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        try:
            if ctx.author.voice and ctx.author.voice.channel == voice_client.channel:
                now = datetime.datetime.now()
                members_data = []

                # Update durations for members still in voice channels
                for member_id, data in voice_data.items():
                    join_time = data['join_time']
                    if join_time:
                        duration = now - join_time
                        data['total_duration'] += duration
                        data['join_time'] = None

                # Sort voice_data by total_duration (descending order)
                sorted_members = sorted(
                    voice_data.items(),
                    key=lambda x: x[1]["total_duration"].total_seconds(),
                    reverse=True
                )

                for member_id, data in sorted_members:
                    member = ctx.guild.get_member(member_id)
                    member_name = member.name if member else f"Unknown member (ID: {member_id})"
                    total_duration = format_time(str(data['total_duration']))
                    members_data.append(f"**{member_name}** was in {data['channel_name']} for: {total_duration}")

                if members_data:
                    log_pages = []
                    numbered_members_data = [f"{i+1}. {member}" for i, member in enumerate(members_data)]
                    for i in range(0, len(numbered_members_data), 10):
                        pages_logs = "\n".join(numbered_members_data[i:i + 10])
                        embed = discord.Embed(
                            title="Time Spent",
                            description=pages_logs,
                            color=discord.Color.teal()
                        )
                        current_page = i // 10 + 1
                        total_pages = (len(numbered_members_data) - 1) // 10 + 1
                        embed.set_footer(text=f"Page {current_page}/{total_pages} | Members who attended: {len(voice_data)}")
                        log_pages.append(embed)

                    attendance_channel = discord.utils.get(ctx.guild.text_channels, name="oculus-attendance")
                    if attendance_channel:
                        view = Paginator(log_pages)
                        await attendance_channel.send(embed=log_pages[0], view=view)
                    else:
                        await ctx.send("The attendance channel cannot cease to exist, I made it this way")
                else:
                    await ctx.send("No voice activity to log.")

                voice_data.clear()
                await voice_client.disconnect()
                await ctx.send(f"{bot.user.name} left the voice channel.")
            else:
                await ctx.send("You are not in the same voice channel as the bot.")
        except Exception as e:
            await ctx.send(f"Error leaving voice channel: {e}")
    else:
        await ctx.send("I am not connected to a voice channel.")

# Command to list durations in real-time
@bot.hybrid_command(name="list", description="Returns a numbered, sorted list of durations")
@commands.has_any_role("Moderator", "Admin")
async def list(ctx):
    await ctx.send("real-time list")
    print("list called")
    load_voice_data()
    now = datetime.datetime.now()
    members_data = []

    # Update durations for members still in voice channels
    for member_id, data in voice_data.items():
        join_time = data['join_time']
        if join_time:
            duration = now - join_time
            data['total_duration'] += duration  # Temporarily update total_duration for real-time calculation
            data['join_time'] = now  # Reset join_time to avoid double-counting

    # Sort voice_data by total_duration (descending order)
    sorted_members = sorted(
        voice_data.items(),
        key=lambda x: x[1]["total_duration"].total_seconds(),
        reverse=True
    )

    for member_id, data in sorted_members:
        member = ctx.guild.get_member(member_id)
        member_name = member.name if member else f"Unknown member (ID: {member_id})"
        total_duration = format_time(str(data['total_duration']))
        members_data.append(f"**{member_name}** was in {data['channel_name']} for: {total_duration}")

    if members_data:
        log_pages = []
        numbered_members_data = [f"{i+1}. {member}" for i, member in enumerate(members_data)]
        for i in range(0, len(numbered_members_data), 10):
            pages_logs = "\n".join(numbered_members_data[i:i + 10])
            embed = discord.Embed(
                title="Time Spent",
                description=pages_logs,
                color=discord.Color.teal()
            )
            current_page = i // 10 + 1
            total_pages = (len(numbered_members_data) - 1) // 10 + 1
            embed.set_footer(text=f"Page {current_page}/{total_pages} | Members who attended: {len(voice_data)}")
            log_pages.append(embed)

        attendance_channel = discord.utils.get(ctx.guild.text_channels, name="oculus-attendance")
        if attendance_channel:
            view = Paginator(log_pages)
            await attendance_channel.send(embed=log_pages[0], view=view)
        else:
            await ctx.send("The attendance channel cannot cease to exist, I made it this way")
    else:
        await ctx.send("No voice activity to log.")

# Command to reset voice data
@bot.hybrid_command(name="reset_data", description="Resets all voice activity data and restarts tracking")
@commands.has_any_role("Moderator", "Admin")
async def reset_data(ctx):
    await ctx.defer()
    global voice_data
    voice_data.clear()
    save_voice_data()  # Save the cleared data to ensure it's persisted

    # Check if the bot is currently in a voice channel
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
        await ctx.send("Voice activity data has been reset, and tracking has restarted for members in the current voice channel.")
    else:
        await ctx.send("Voice activity data has been reset. The bot is not currently in a voice channel, so no members are being tracked.")

# Help command
@bot.hybrid_command(name="help_me", description="Well, I hope it'll help")
@commands.has_any_role("Moderator", "Admin")
async def help_me(ctx):
    await ctx.send("/join: Makes the bot enter the voice channel you're in.\n/leave: The bot leaves the voice channel, you need to be in the VC for it to work; it calculates the time spent by each member and logs it.\n/list: Real-time list.\n/reset_data: Resets all voice activity data and restarts tracking.")

# Run the bot
bot.run(TOKEN)
