from dataclasses import dataclass

from Options import Choice, DeathLink, PerGameCommonOptions, Range, Toggle


class Goal(Choice):
    """
    Determines the win condition.
    Government Lab: Clear the Government Lab with all 5 keys.
    All Tapes: Complete all 11 stage tapes.
    Boss Rush: Defeat all 4 bosses (V, Kissyface, Headhunter, Psychiatrist).
    """
    display_name = "Goal"
    option_government_lab = 0
    option_all_tapes = 1
    option_boss_rush = 2
    default = 0


class StartingTape(Choice):
    """
    The initial VHS Tape granted to the player at game start.
    Allows accessing the chosen stage immediately.
    """
    display_name = "Starting Tape"
    option_factory = 0
    option_hotel = 1
    option_club = 2
    option_prison = 3
    option_studio_51 = 4
    option_mansion = 5
    option_chinatown = 6
    option_dragon = 7
    option_slaughterhouse = 8
    option_bunker = 9
    option_random = 10
    default = 0


class RequiredTapes(Range):
    """
    Number of VHS Tapes that must be collected to access the Psychiatrist's Office.
    """
    display_name = "Required Tapes for Psychiatrist"
    range_start = 1
    range_end = 11
    default = 8


class ShuffleSwords(Toggle):
    """
    Whether the 5 swords are shuffled into the item pool as useful items.
    """
    display_name = "Shuffle Swords"
    default = Toggle.option_true


class Enemysanity(Toggle):
    """
    Whether every non-boss, non-optional enemy in the game counts as a check.
    Defeating the enemy immediately grants the check item.
    Adds 487 item locations across all 10 stages.
    """
    display_name = "Enemysanity"
    default = Toggle.option_false


class TrapPercentage(Range):
    """
    Percentage of filler items that are replaced with trap items.
    Traps include Chronos Overdose, Freeze Trap, Chronos Disruptor,
    Screen Flip, Spatial Warp, Roll Disruptor, and Pacifist Trap.
    """
    display_name = "Trap Percentage"
    range_start = 0
    range_end = 100
    default = 10


class DeathLinkAmnesty(Range):
    """
    Number of deaths that can accumulate before a DeathLink signal is sent
    to other players. Set to 0 to send on every death. Only takes effect
    when DeathLink is enabled.
    """
    display_name = "DeathLink Amnesty"
    range_start = 0
    range_end = 30
    default = 0


class RandomizeMusic(Toggle):
    """
    Randomize and shuffle background music tracks across all stages,
    cutscenes, and boss fights.
    """
    display_name = "Randomize Music"
    default = Toggle.option_false


class RandomizeSFX(Toggle):
    """
    Randomize and shuffle all sound effects in the game.
    Every sword slash, gunshot, explosion, enemy death, and menu sound
    will be randomized for chaos!
    """
    display_name = "Randomize Sound Effects"
    default = Toggle.option_false


@dataclass
class KatanaZeroOptions(PerGameCommonOptions):
    goal: Goal
    starting_tape: StartingTape
    required_tapes: RequiredTapes
    shuffle_swords: ShuffleSwords
    enemysanity: Enemysanity
    trap_percentage: TrapPercentage
    death_link: DeathLink
    death_link_amnesty: DeathLinkAmnesty
    randomize_music: RandomizeMusic
    randomize_sfx: RandomizeSFX
