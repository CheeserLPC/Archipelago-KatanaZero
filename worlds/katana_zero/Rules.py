"""Access rules for Katana ZERO Archipelago world."""

from __future__ import annotations

from typing import TYPE_CHECKING

from worlds.generic.Rules import add_rule, set_rule

if TYPE_CHECKING:
    from . import KatanaZeroWorld

# The 11 stage tape names (matches item names without the "Tape: " prefix).
TAPE_NAMES: list[str] = [
    "Factory",
    "Hotel",
    "Club",
    "Prison",
    "Studio 51",
    "Mansion",
    "Chinatown",
    "Dragon",
    "Slaughterhouse",
    "Bunker",
    "Government Lab",
]

# All 5 Government Lab keys.
ALL_KEYS: list[str] = [
    "Prism Key",
    "Master Key",
    "Prototype Key",
    "Phoenix Key",
    "Savant Key",
]

# Mapping of level region name → required tape item name.
_ENTRANCE_TAPE_MAP: dict[str, str] = {
    "Factory Hideout":      "Tape: Factory",
    "Murdower Hotel":       "Tape: Hotel",
    "Club Neon":            "Tape: Club",
    "Mutual-Nil Prison":    "Tape: Prison",
    "Studio 51":            "Tape: Studio 51",
    "Mansion Hideout":      "Tape: Mansion",
    "Chinatown":            "Tape: Chinatown",
    "Dragon Tape":          "Tape: Dragon",
    "Slaughterhouse":       "Tape: Slaughterhouse",
    "Bunker":               "Tape: Bunker",
    "Government Lab":       "Tape: Government Lab",
}


def set_rules(world: "KatanaZeroWorld") -> None:
    """Apply all entrance and location access rules."""
    multiworld = world.multiworld
    player = world.player

    # ── Entrance rules (tape gating) ──────────────────────────────────────────
    for region_name, tape_item in _ENTRANCE_TAPE_MAP.items():
        entrance = multiworld.get_entrance(f"Menu -> {region_name}", player)
        set_rule(entrance, lambda state, t=tape_item, p=player: state.has(t, p))

    # Psychiatrist's Office requires enough tapes.
    psych_entrance = multiworld.get_entrance("Menu -> Psychiatrist's Office", player)
    required_tapes = world.options.required_tapes.value
    set_rule(
        psych_entrance,
        lambda state, p=player, req=required_tapes: sum(
            state.has(f"Tape: {t}", p) for t in TAPE_NAMES
        ) >= req,
    )

    # ── Location rules (mechanic requirements) ────────────────────────────────

    # Helper to reduce repetition.
    def _require(location_name: str, *items: str) -> None:
        """Add a rule requiring all *items* for the given location."""
        loc = multiworld.get_location(location_name, player)
        add_rule(loc, lambda state, reqs=items, p=player: all(state.has(r, p) for r in reqs))

    # Factory Hideout
    _require("Factory - Tape Completed",    "Wall Jump")
    _require("Factory - Rooftop Reached",   "Wall Jump")
    _require("Factory - Left Roof Corpse",  "Wall Jump")

    # Murdower Hotel (rolls are native)
    # _require("Hotel - Penthouse Reached")
    # _require("Hotel - Penthouse Assassination")

    # Club Neon
    _require("Club - Tape Completed",  "Strength Training")

    # Studio 51
    _require("Studio 51 - Tape Completed",    "Deflect")
    _require("Studio 51 - Backstage Reached", "Deflect")

    # Mansion Hideout
    _require("Mansion - Tape Completed",  "Wall Jump")
    _require("Mansion - Attic Reached",   "Wall Jump")
    _require("Mansion - Robber's Sack",   "Wall Jump")

    # Slaughterhouse
    _require("Slaughterhouse - Camera Room",         "Chronos")
    _require("Slaughterhouse - Camera Room Reached",  "Chronos")

    # Bunker
    _require("Bunker - Tape Completed",     "Deflect")
    _require("Bunker - Deep Bunker Reached", "Deflect")

    # Boss defeats
    _require("V Defeated",            "Deflect")
    _require("Headhunter Defeated",   "Deflect")
    _require("Psychiatrist Defeated", "Deflect")

    # Government Lab – requires all 5 keys
    _require("Government Lab - Tape Completed", *ALL_KEYS)

    # ── Enemysanity Rules ─────────────────────────────────────────────────────
    if world.options.enemysanity.value:
        from .enemy_data import ENEMY_CHECKS
        for enemy in ENEMY_CHECKS:
            if enemy.room in ("room_factory_3", "room_factory_3_2", "room_factory_4"):
                _require(enemy.name, "Wall Jump")
            elif enemy.room == "room_mansion_4":
                _require(enemy.name, "Wall Jump")

    # ── Victory condition ─────────────────────────────────────────────────────
    goal = world.options.goal.value

    if goal == 0:  # government_lab
        multiworld.completion_condition[player] = lambda state, p=player: (
            state.has("Tape: Government Lab", p)
            and state.has_all(ALL_KEYS, p)
        )
    elif goal == 1:  # all_tapes
        all_tapes = [f"Tape: {t}" for t in TAPE_NAMES]
        multiworld.completion_condition[player] = lambda state, p=player, tapes=all_tapes: (
            state.has_all(tapes, p)
        )
    elif goal == 2:  # boss_rush
        boss_locations = [
            "V Defeated",
            "Kissyface Defeated",
            "Headhunter Defeated",
            "Psychiatrist Defeated",
        ]
        multiworld.completion_condition[player] = lambda state, p=player, bosses=boss_locations: all(
            state.can_reach_location(b, p) for b in bosses
        )
