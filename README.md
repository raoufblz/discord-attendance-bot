# OCULUS
![a1613327-09bd-44f9-8147-de5070be9a7c3](https://github.com/user-attachments/assets/78b1dfa6-207f-4e5d-b200-c0e4d30006a7)

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python Version">
  </a>
  <a href="https://discordpy.readthedocs.io/">
    <img src="https://img.shields.io/badge/discord.py-2.3%2B-green" alt="Discord.py Version">
  </a>
  <a href="https://github.com/theskumar/python-dotenv">
    <img src="https://img.shields.io/badge/python--dotenv-1.1.0-yellow" alt="python-dotenv Version">
  </a>
</p>

**A voice activity tracking Discord bot that logs member participation and generates time-based reports**

**README file still in developement 🔨🔨🔨**

## Features:
🔊 **Voice Tracking:**  
- Records time spent by members in voice channels
- Tracks bot connection status and member join/leave events

📔 **Persistent Logging:**  
- Automatic `voice_data.json` storage
- Recreates deleted logging channel (`#project-oculus`)

💻 **Command Suite:**  
- `/join` - Connects to your voice channel
- `/leave` - Disconnects and generates reports
- `/list` - Shows real-time tracking data
- `/reset_data` - Clears all stored activity data
- `/help_me` - Command documentation

:accessibility: **Access Control:**  
- Role restrictions: Moderator/Admin roles only
- Channel protection: Critical logging channel can't be deleted

## Installation: (in developement 🔨🔨)

1. **Clone Repository:**  
```bash
git clone https://github.com/raoufblz/discord-attendance-bot.git
cd discord-attendance-bot
```
2. **Set Up Environment:**
    create a .env file for your bot token:
```env
TOKEN=insert_your_discord_bot_token_here
```
3. **Install dependencies:**
```
pip install -r requirements.txt
```
4. **start the bot:**
```
python .\main.py
```

## Usage: (in developement 🔨🔨)

- the bot creates a text channel to log the pagination to, even if deleted it recreates it.
- provided that you re in a voice channel use `/join` to invite the bot to that channel, the bot will start tracking from that time.
- you could use `/list` to see real-time voice data without losing track of it.
- once you want the bot to stop tracking the time, use `/leave`, the bot will leave the voice channel and log the pagination of the members who were present during its presence, sorted by their total duration.
- in case you need to delete the voice data or restart tracking, use `/reset_data` to delete all past data and start anew.
- in case you forget any of these commands or what they do, use the `/help` command.

## Command documentation: (in developement 🔨🔨)
- every command is a slash command (Discord's prefered way).
- the commands have role-based access; only those with specefic roles can use them.

- /join: makes the bot enter the voice channel you re in.
- /leave: the bot leaves the voice channel, you need to be in the vc for it to work,
    it calculates the time spent by each member and logs it as a Discord pagination.
- /list: logs real-time voice data in the bot specefic channel.
- /help: lists all available commands and what they do.
- /reset_data: deletes all past voice data and restarts tracking.

