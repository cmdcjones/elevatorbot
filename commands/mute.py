import asyncio
import random
import aiohttp
import io
import discord

from commands.base_command import BaseCommand
from functions.miscFunctions import hasAdminOrDevPermissions
from functions.roleLookup import assignRolesToUser, removeRolesFromUser
from static.globals import muted_role_id


class mute(BaseCommand):
    def __init__(self):
        # A quick description for the help message
        description = "[Admin] Mutes mentioned user for x hours"
        params = ["hours"]
        super().__init__(description, params)

    # Override the handle() method
    # It will be called every time the command is received
    async def handle(self, params, message, mentioned_user, client):
        # check for perms
        if not await hasAdminOrDevPermissions(message):
            return

        # check that sb got mentioned
        if mentioned_user == message.author:
            await message.reply("You can't mute yourself :)")
            return

        # check that parms are correct
        if not len(params) == 1:
            await message.reply("Incorrect parameters, please try again")
            return

        # check that hours is int
        try:
            hours = int(params[0])
        except ValueError:
            await message.reply("Incorrect parameters, please try again")
            return

        status = await message.reply(f"Muted {mentioned_user.mention} for {hours} hours.\nI will edit this message once the time is over.")
        await assignRolesToUser([muted_role_id], mentioned_user, message.guild)
        await asyncio.sleep(hours*60*60)
        await removeRolesFromUser([muted_role_id], mentioned_user, message.guild)
        await status.edit(f"{mentioned_user.mention} is no longer muted.")


# has been slashified
class muteMe(BaseCommand):
    def __init__(self):
        # A quick description for the help message
        description = "I wonder what this does..."
        params = []
        super().__init__(description, params)

    # Override the handle() method
    # It will be called every time the command is received
    async def handle(self, params, message, mentioned_user, client):
        await message.channel.send("If you insist...")
        if message.author.id is not mentioned_user.id:
            await message.channel.send("I saw what you did there, that doesn't work here mate")
        await message.author.send("Introducing a new feature: **gambling!**")
        await asyncio.sleep(1)
        await message.author.send("Let me roll the dice for you, I can't wait to see if you win the jackpot")
        await asyncio.sleep(2)
        await message.author.send("_Rolling dice..._")
        await asyncio.sleep(5)
        timeout = random.choice([5, 10, 15, 30, 45, 60, 120])
        if timeout == 120:
            await message.author.send("**__!!! CONGRATULATIONS !!!__**")
            async with aiohttp.ClientSession() as session:
                async with session.get("https://media.istockphoto.com/videos/amazing-explosion-animation-with-text-congratulations-video-id1138902499?s=640x640") as resp:
                    if resp.status == 200:
                        data = io.BytesIO(await resp.read())
                        await message.author.send(file=discord.File(data, 'congratulations.png'))

            await message.author.send(f"You won the jackpot! That's a timeout of **{timeout} minutes** for you, enjoy!")
        else:
            await message.author.send(f"You won a timout of **{timeout} minutes**, congratulations!!!")
            await asyncio.sleep(2)
            await message.author.send("Better luck next time if you were hunting for the jackpot")

        # add muted role
        print(f"Muting {message.author.display_name} for {timeout} minutes")
        await assignRolesToUser([muted_role_id], message.author, message.guild)

        # remove muted role after an hour
        await asyncio.sleep(60 * timeout)
        await removeRolesFromUser([muted_role_id], message.author, message.guild)
        await message.author.send("Sadly your victory is no more. Hope to see you back again soon!")
