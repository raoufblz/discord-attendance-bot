"""
discord bot made by _raouf_blz_ *still under development (maybe??)*
    - returns a pagination with a numbered, sorted list of members who were in a 
    voice-channel, how much time each of them spent and how many they were.
    - creates a text channel to log the pagination to, even if deleted it recreates it.
    - /join: makes the bot enter the voice channel you re in.
    - /leave: the bot leaves the voice channel, you need to be in the vc for it to work,
    it calculates the time spent by each member and logs it.
    - the commands have role-based access.
    - saves data in case of connection problems, deletes all previous data only if /leave
    is executed.
"""

import discord
from discord.ext import commands
import datetime
from discord.ui import Button, View
import json
import asyncio
from bottoken import TOKEN                  # token

intents = discord.Intents.default()
intents.message_content = True              # read messages
intents.members = True                      # access members
intents.voice_states = True                 # track voice state changes

bot = commands.Bot(command_prefix='/', intents=intents)
voice_data = {}

#########################################<{json}>##############################################
# Save voice_data to a file
def save_voice_data():
    try:
        with open("voice_data.json", "w") as f:
            json.dump(
                {str(k): {
                    "join_time": v["join_time"].isoformat() if v["join_time"] else None,  # Store None as null
                    "total_duration": str(v["total_duration"].total_seconds()),
                    "channel_name": v["channel_name"]
                } for k, v in voice_data.items()},
                f
            )
        print("Voice data saved.")
    except Exception as e:
        print(f"Error saving voice data: {e}")


# Load voice_data from a file
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

##############################################################################################

@bot.event
async def on_ready():
    global voice_data
    voice_data = load_voice_data()
    print(f'We have logged in as {bot.user}')

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

    # start the periodic save task
    bot.loop.create_task(periodic_save())

    # track existing voice channel members
    for guild in bot.guilds:
        for voice_channel in guild.voice_channels:
            for member in voice_channel.members:
                if member.id not in voice_data:
                    voice_data[member.id] = {
                        "join_time": datetime.datetime.now(),
                        "total_duration": datetime.timedelta(),
                        "channel_name": voice_channel.name
                    }
                else:
                    voice_data[member.id]["join_time"] = datetime.datetime.now()
                    voice_data[member.id]["channel_name"] = voice_channel.name
    print("Tracking existing voice channel members, we tracking everyone'round here...")


@bot.event
async def on_resumed():
    global voice_data
    voice_data = load_voice_data()
    print(f"{bot.user} reconnected to Discord.")


@bot.event
async def on_disconnect():
    print(f"{bot.user} disconnected from Discord.")
    save_voice_data()


async def periodic_save():
    await bot.wait_until_ready()
    while not bot.is_closed():
        save_voice_data()
        print("Voice data saved.")
        await asyncio.sleep(30)             # saves data every 30 sec (adjust as needed)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)     # process commands


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


@bot.command()
@commands.has_any_role("Moderator", "Admin")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            await channel.connect()
            await ctx.send(f"{bot.user.name} joined voice channel: {channel.name}")
        except Exception as e:
            await ctx.send(f"Error joining voice channel: {e}")
    else:
        await ctx.send("You are not connected to a voice channel.")


@bot.event
async def on_voice_state_update(member, before, after):
    now = datetime.datetime.now()

    # check if the user joined a voice channel
    if before.channel is None and after.channel is not None:
        # initialize or reset the user's data
        if member.id not in voice_data:
            voice_data[member.id] = {
                "join_time": now,
                "total_duration": datetime.timedelta(),
                "channel_name": after.channel.name
            }
        else:
            voice_data[member.id]["join_time"] = now
            voice_data[member.id]["channel_name"] = after.channel.name
        print(f'{member.name} joined voice channel {after.channel.name} at {now}')

    # check if the user left a voice channel
    elif before.channel is not None and after.channel is None:
        if member.id in voice_data:
            # calculate the duration of the current session
            join_time = voice_data[member.id]['join_time']
            if join_time:  # ensures they were actually in a voice channel
                duration = now - join_time
                voice_data[member.id]['total_duration'] += duration
                # set join_time to None to indicate they are no longer in a voice channel
                voice_data[member.id]['join_time'] = None
            print(f'{member.name} left voice channel {before.channel.name} at {now}')


def format_time(input_time):
    hours, minutes, seconds = input_time.split(":")
    seconds, fractional = seconds.split(".")
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    fractional = float(f"0.{fractional}")
    total_seconds = fractional + seconds
    formatted_time = f"{hours} hr(s) {minutes} min(s) {total_seconds:.2f} sec(s)"
    return formatted_time


class Paginator(View):
    def __init__(self, pages):
        super().__init__(timeout=None)      # we don't need a timeout, maybe if the bot dies
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction):
        """Update the message with the current page."""
        self.previous.disabled = self.current_page == 0                  # disable
        self.next.disabled = self.current_page == len(self.pages) - 1    # disable
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)   # no aquamarine :(
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)


@bot.command()
@commands.has_any_role("Moderator", "Admin")
async def leave(ctx):
    save_voice_data()
    await asyncio.sleep(0)
    voice_client = ctx.voice_client
    if voice_client:
        try:
            # checks if the command issuer (do they say issuer?) is in the same voice channel as the bot
            if ctx.author.voice and ctx.author.voice.channel == voice_client.channel:
                now = datetime.datetime.now()
                members_data = []

                # update durations for members still in voice channels
                for member_id, data in voice_data.items():
                    join_time = data['join_time']
                    if join_time:
                        duration = now - join_time
                        data['total_duration'] += duration
                        data['join_time'] = None  # reset join_time

                # sort voice_data by total_duration (descending order)
                sorted_members = sorted(
                    voice_data.items(),
                    key=lambda x: x[1]["total_duration"].total_seconds(),
                    reverse=True
                )

                for member_id, data in sorted_members:
                    member = ctx.guild.get_member(member_id)  # retrieve the member object
                    if member:
                        member_name = member.name
                    else:
                        member_name = f"Unknown member (ID: {member_id})"  # if member is no longer in the guild

                    # retrieve the total_duration
                    total_duration = data['total_duration']
                    total_duration = format_time(str(total_duration))

                    # append the member's data to the log
                    members_data.append(f"**{member_name}** was in {data['channel_name']} for: {total_duration}")

                if members_data:
                    log_pages = []
                    #add numbers next to em
                    numbered_members_data = [f"{i+1}. {member}" for i, member in enumerate(members_data)]
                    for i in range(0, len(numbered_members_data), 10):
                        pages_logs = "\n".join(numbered_members_data[i:i + 10])
                        embed = discord.Embed(
                            title="Time Spent",
                            description=pages_logs,
                            color=discord.Color.teal()                            # dm me when they add aquamarine
                        )  
                        # change all 10s to x if you want x member by page
                        current_page = i // 10 + 1                                # Convert zero-based index to one-based page number
                        total_pages = (len(numbered_members_data) - 1) // 10 + 1  # Total pages (ceiling division)
                        embed.set_footer(text=f"Page {current_page}/{total_pages}  |  Members who attended: {len(voice_data)}")
                        log_pages.append(embed)

                    if discord.utils.get(ctx.guild.text_channels, name="oculus-attendance"):
                        view = Paginator(log_pages)
                        await discord.utils.get(ctx.guild.text_channels, name="oculus-attendance").send(embed=log_pages[0], view=view)
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
        
bot.run(TOKEN)
