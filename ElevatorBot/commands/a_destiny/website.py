from naff import ActionRow, Button, ButtonStyles, Member, OptionTypes, SlashCommandChoice, slash_command, slash_option

from ElevatorBot.commandHelpers.optionTemplates import default_user_option
from ElevatorBot.commands.base import BaseModule
from ElevatorBot.discordEvents.customInteractions import ElevatorInteractionContext
from ElevatorBot.networking.destiny.account import DestinyAccount
from ElevatorBot.networking.destiny.profile import DestinyProfile


class Website(BaseModule):
    system_to_name = {1: "xb", 2: "ps", 3: "pc"}

    @slash_command(
        name="website",
        description="Gets your personalised link to curated Destiny 2 stat websites",
        dm_permission=False,
    )
    @slash_option(
        name="website",
        description="The website you want a personalised link for",
        required=True,
        opt_type=OptionTypes.STRING,
        choices=[
            SlashCommandChoice(name="Braytech", value="Braytech"),
            SlashCommandChoice(name="D2 Checklist", value="D2 Checklist"),
            SlashCommandChoice(name="Destiny Tracker", value="Destiny Tracker"),
            SlashCommandChoice(name="Dungeon Report", value="Dungeon Report"),
            SlashCommandChoice(name="Grandmaster Report", value="Grandmaster Report"),
            SlashCommandChoice(name="Nightfall Report", value="Nightfall Report"),
            SlashCommandChoice(name="Strike Report", value="Strike Report"),
            SlashCommandChoice(name="Raid Report", value="Raid Report"),
            SlashCommandChoice(name="Solo Report", value="Solo Report"),
            SlashCommandChoice(name="Expunge Report", value="Expunge Report"),
            SlashCommandChoice(name="Trials Report", value="Trials Report"),
            SlashCommandChoice(name="Triumph Report", value="Triumph Report"),
            SlashCommandChoice(name="Wasted on Destiny", value="Wasted on Destiny"),
            SlashCommandChoice(name="Crucible Report", value="Crucible Report"),
        ],
    )
    @default_user_option()
    async def website(self, ctx: ElevatorInteractionContext, website: str, user: Member = None):
        member = user or ctx.author

        # get destiny info
        destiny_profile = DestinyProfile(ctx=ctx, discord_member=member, discord_guild=ctx.guild)
        destiny_player = await destiny_profile.from_discord_member()

        # get the text
        match website:
            case "Solo Report":
                text = f"https://elevatorbot.ch/soloreport/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Expunge Report":
                text = f"https://elevatorbot.ch/expungereport/{self.system_to_name[destiny_player.system]}/{destiny_player.destiny_id}"

            case "Raid Report":
                text = f"https://raid.report/{self.system_to_name[destiny_player.system]}/{destiny_player.destiny_id}"

            case "Dungeon Report":
                text = (
                    f"https://dungeon.report/{self.system_to_name[destiny_player.system]}/{destiny_player.destiny_id}"
                )

            case "Grandmaster Report":
                text = f"https://grandmaster.report/user/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Nightfall Report":
                text = f"https://nightfall.report/guardian/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Strike Report":
                text = f"https://strike.report/{self.system_to_name[destiny_player.system]}/{destiny_player.destiny_id}"

            case "Trials Report":
                text = f"https://destinytrialsreport.com/report/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Triumph Report":
                text = f"https://triumph.report/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Braytech":
                text = f"https://bray.tech/{destiny_player.system}/{destiny_player.destiny_id}"

                destiny_account = DestinyAccount(ctx=ctx, discord_member=member, discord_guild=ctx.guild)
                characters = await destiny_account.get_character_info()

                if characters.characters:
                    text += f"/{characters.characters[0].character_id}/weeklies"

            case "D2 Checklist":
                text = f"https://www.d2checklist.com/{destiny_player.system}/{destiny_player.destiny_id}"

            case "Destiny Tracker":
                text = (
                    f"https://destinytracker.com/destiny-2/profile/{destiny_player.system}/{destiny_player.destiny_id}"
                )

            case "Crucible Report":
                text = f"https://crucible.report/{destiny_player.system}/{destiny_player.destiny_id}"

            # Wasted on Destiny
            case _:
                text = f"https://wastedondestiny.com/{destiny_player.system}_{destiny_player.destiny_id}"

        components = [
            ActionRow(
                Button(
                    style=ButtonStyles.URL,
                    label=f"{member.display_name} - {website}",
                    url=text,
                ),
            ),
        ]
        await ctx.send(components=components)


def setup(client):
    Website(client)
