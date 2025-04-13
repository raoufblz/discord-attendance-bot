import json
import datetime
import asyncio
import discord
from discord.ui import Button, View
from shared import voice_data, bot

# save voice_data to a JSON file
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

# load voice_data from a JSON file
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

# periodically save voice_data
async def periodic_save():
    await bot.wait_until_ready()
    while not bot.is_closed():
        save_voice_data()
        print("Voice data saved (periodic save)")
        await asyncio.sleep(30)  # save every 30 secs


def format_time(input_time):
    try:
        # checks if input_time is a timedelta object
        if isinstance(input_time, datetime.timedelta):
            total_seconds = input_time.total_seconds()
        # checks if input_time is a string representation of a timedelta
        elif isinstance(input_time, str):
            if ":" in input_time:
                hours, minutes, seconds = map(float, input_time.split(":"))
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                # try to pass as float
                total_seconds = float(input_time)
        else:
            # fallback for other types
            total_seconds = float(input_time)
            
        # formats the time
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = float(total_seconds % 60)
        return f"{hours} hr(s) {minutes} min(s) {seconds:.2f} sec(s)"
    except Exception as e:
        print(f"Error formatting time: {e}")
        return "Invalid time format"


async def ensure_bot_channel(guild):
    attendance_channel = discord.utils.get(guild.text_channels, name="project-oculus")
    if not attendance_channel:
        try:
            # creates the attendance channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                guild.me: discord.PermissionOverwrite(send_messages=True)
            }
            attendance_channel = await guild.create_text_channel("project-oculus", overwrites=overwrites)
            await attendance_channel.send("This channel logs the time spent by members in voice chats.")
            print(f"Created 'project-oculus' channel in guild: {guild.name}")
        except Exception as e:
            print(f"Error creating project-oculus channel in guild {guild.name}: {e}")
    return attendance_channel

# creates paginated time logs and sends it to the channel
async def send_paginated_time_logs(interaction_or_ctx, members_data):
    if not members_data:
        # checks if we're dealing with an Interaction or a Context
        if isinstance(interaction_or_ctx, discord.Interaction):
            await interaction_or_ctx.followup.send("No voice activity to log.")
        else:
            await interaction_or_ctx.send("No voice activity to log.")
        return
        
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

    # get the guild from either interaction or context
    guild = getattr(interaction_or_ctx, 'guild', None)
    attendance_channel = await ensure_bot_channel(guild)
    
    if attendance_channel:
        view = Paginator(log_pages)
        await attendance_channel.send(embed=log_pages[0], view=view)
    else:
        # checks if we're dealing with an Interaction or Context
        if isinstance(interaction_or_ctx, discord.Interaction):
            await interaction_or_ctx.followup.send("The attendance channel cannot cease to exist, I made it this way")
        else:
            await interaction_or_ctx.send("The attendance channel cannot cease to exist, I made it this way")

# Paginator class for paginated embeds
class Paginator(View):
    def __init__(self, pages):
        super().__init__(timeout=None)
        self.pages = pages
        self.current_page = 0

    async def update_message(self, interaction):
        """Update the message with the current page."""
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page == len(self.pages) - 1
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)
