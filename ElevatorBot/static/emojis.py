from dis_snek.errors import Forbidden
from dis_snek.models import CustomEmoji


class __ElevatorEmojis:
    """To add an emoji add it to the class variables"""

    def __init__(self):
        # Descend Font
        self.tile_left: CustomEmoji | int = 768906489309822987
        self.tile_mid: CustomEmoji | int = 768906489103384657
        self.tile_right: CustomEmoji | int = 768906489729122344

        self.yes: CustomEmoji | int = 768908985557844028
        self.question: CustomEmoji | int = 768906489686655016
        self.enter: CustomEmoji | int = 768906489103384688
        self.circle: CustomEmoji | int = 768906489464619008

        self.destiny: CustomEmoji | int = 768906489472876574
        self.descend_logo: CustomEmoji | int = 768907515193720874
        self.elevator_logo: CustomEmoji | int = 768907515386921020

        self.kinetic: CustomEmoji | int = 906180170875031562
        self.stasis: CustomEmoji | int = 897797463799369769
        self.arc: CustomEmoji | int = 897797463933583401
        self.solar: CustomEmoji | int = 897797463937798174
        self.void: CustomEmoji | int = 897797464013307905

        self.unstoppable: CustomEmoji | int = 897797463807774752
        self.barrier: CustomEmoji | int = 897797463988142091
        self.overload: CustomEmoji | int = 897797463988142090

        self.auto_rifle: CustomEmoji | int = 906180170778546226
        self.shotgun: CustomEmoji | int = 906180170971484220
        self.machine_gun: CustomEmoji | int = 906180170833100820
        self.hand_cannon: CustomEmoji | int = 906180170979881000
        self.rocket_launcher: CustomEmoji | int = 906180170799521812
        self.fusion_rifle: CustomEmoji | int = 906180170929565777
        self.sniper_rifle: CustomEmoji | int = 906180170807906366
        self.pulse_rifle: CustomEmoji | int = 906180170820485190
        self.scout_rifle: CustomEmoji | int = 906180170858250261
        self.sidearm: CustomEmoji | int = 906180170833096774
        self.sword: CustomEmoji | int = 906180170929565776
        self.linear_fusion_rifle: CustomEmoji | int = 906180170807906365
        self.grenade_launcher: CustomEmoji | int = 906180170405249025
        self.submachine_gun: CustomEmoji | int = 906180170799521815
        self.trace_rifle: CustomEmoji | int = 912989912251367444
        self.bow: CustomEmoji | int = 906180170799538206

        self.primary: CustomEmoji | int = 906180170887622656
        self.special: CustomEmoji | int = 906180170858250260
        self.heavy: CustomEmoji | int = 906180170451410985

        # Emote Server
        self.among_us: CustomEmoji | int = 905844106914332682
        self.barotrauma: CustomEmoji | int = 905846654316445758
        self.gta: CustomEmoji | int = 905847049059197009
        self.valorant: CustomEmoji | int = 905849958601744385
        self.lol: CustomEmoji | int = 905843726583226449
        self.eft: CustomEmoji | int = 905846654211620865
        self.minecraft: CustomEmoji | int = 905846654211620866
        self.new_world: CustomEmoji | int = 900640805784522762

        self.warlock: CustomEmoji | int = 830747907488612402
        self.hunter: CustomEmoji | int = 830747907829006346
        self.titan: CustomEmoji | int = 830747907576823808
        self.light_level_icon: CustomEmoji | int = 830750430816108564

        self.join: CustomEmoji | int = 850000522101391400
        self.leave: CustomEmoji | int = 850000522048045106
        self.backup: CustomEmoji | int = 850000522107027466

        self.zoom: CustomEmoji | int = 906503515642425396
        self.ping_sock: CustomEmoji | int = 586436224013565992

        # Descend [Test 01]

        # Descend [Test 02]
        self.thumps_up: CustomEmoji | int = 754946723612196975
        self.thumps_down: CustomEmoji | int = 754946723503276124

    async def init_emojis(self, client):
        """Runs on startup to get the emojis we use"""

        emojis = []

        # get all emojis from the emote servers
        for guild_id in [768902336914391070, 724676552175910934, 556418279015448596, 697720309847162921]:
            try:
                guild = await client.get_guild(guild_id)
                emojis.extend(await guild.get_all_custom_emojis())
            except Forbidden:
                continue

        # loop through found emojis
        for emoji in emojis:
            # loop through all class attributes
            # this is inefficient but dynamic and only called once
            for attr, value in self.__dict__.items():
                if isinstance(value, int):
                    if emoji.id == value:
                        setattr(self, attr, emoji)


custom_emojis: __ElevatorEmojis = __ElevatorEmojis()
