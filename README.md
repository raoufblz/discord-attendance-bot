- returns a pagination with a numbered, sorted list of members who were in a 
    voice-channel, how much time each of them spent and how many they were.
- creates a text channel to log the pagination to, even if deleted it recreates it.
- /join: makes the bot enter the voice channel you re in.
- /leave: the bot leaves the voice channel, you need to be in the vc for it to work,
    it calculates the time spent by each member and logs it.
- the commands have role-based access.
- saves data in case of connection problems, deletes all previous data only if /leave
    is executed.
