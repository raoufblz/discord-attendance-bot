### OCULUS
![a1613327-09bd-44f9-8147-de5070be9a7c3](https://github.com/user-attachments/assets/78b1dfa6-207f-4e5d-b200-c0e4d30006a7)

- returns a pagination with a numbered, sorted list of members who were in a 
    voice-channel, how much time each of them spent and how many they were.
- creates a text channel to log the pagination to, even if deleted it recreates it.
- /join: makes the bot enter the voice channel you re in.
- /leave: the bot leaves the voice channel, you need to be in the vc for it to work,
    it calculates the time spent by each member and logs it.
- the commands have role-based access.
- /list: logs real-time voice data in a channel the bot creates.
- /help: a command that lists all available commands and what they do.
- every command is now a slash command (Discord's prefered way).
- /reset_data: deletes all past voice data and restarts tracking.
- saves data in case of connection problems, deletes all previous data only if /leave
    is executed.
