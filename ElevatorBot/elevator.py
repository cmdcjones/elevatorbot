import os

import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from ElevatorBot.discordEvents.base import register_discord_events
from ElevatorBot.misc.initBackgroundEvents import register_background_events
from ElevatorBot.misc.initLogging import init_logging
from settings import DISCORD_BOT_TOKEN, SYNC_COMMANDS


first_start = True

# config logging
init_logging()

# print ascii art
print("----------------------------------------------------------------------------------------")
print(
    """
      ______   _                          _                    ____            _   
     |  ____| | |                        | |                  |  _ \          | |  
     | |__    | |   ___  __   __   __ _  | |_    ___    _ __  | |_) |   ___   | |_ 
     |  __|   | |  / _ \ \ \ / /  / _` | | __|  / _ \  | '__| |  _ <   / _ \  | __|
     | |____  | | |  __/  \ V /  | (_| | | |_  | (_) | | |    | |_) | | (_) | | |_ 
     |______| |_|  \___|   \_/    \__,_|  \__|  \___/  |_|    |____/   \___/   \__|                                                                          
    """
)
print("----------------------------------------------------------------------------------------\n")
print("Starting Up...")

# enable intents to allow certain events
intents = discord.Intents.default()
intents.members = True
intents.guilds = True


# define on_ready event
class ElevatorBot(Bot):
    async def on_ready(
        self
    ):
        # only run this on first startup
        global first_start
        if not first_start:
            return
        first_start = False

        print("Startup Finished!\n")
        print("--------------------------\n")


# actually get the bot obj
client = ElevatorBot(
    intents=intents,
    help_command=None,
    command_prefix="!",
    owner_ids=[
        238388130581839872,
        219517105249189888,
    ],
)
slash_client = SlashCommand(client, sync_commands=SYNC_COMMANDS)

# add discord events and handlers
register_discord_events(client, slash_client)

# load commands
print("Loading Commands...")
slash_dir = "commands"
for file in os.listdir(slash_dir):
    if file.endswith(".py") and not file.startswith("__init__"):
        file = file.removesuffix(".py")
        extension = f"{slash_dir}.{file}"
        client.load_extension(extension)
print(f"< {len(slash_client.commands)} > Commands Loaded")

# load context menus
print("Loading Context Menus...")
context_dir = "contextMenus"
for root, dirs, files in os.walk(context_dir):
    for file in files:
        if file.endswith(".py") and not file.startswith("__init__"):
            file = file.removesuffix(".py")
            path = os.path.join(root, file)
            client.load_extension(path.replace("/", ".").replace("\\", "."))

# add background events
print("Loading Background Events...")
events_loaded = register_background_events(client)
print(f"< {events_loaded} > Background Events Loaded")

# run the bot
client.run(DISCORD_BOT_TOKEN)
