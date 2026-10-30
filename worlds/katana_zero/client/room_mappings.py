"""Room and check mappings for Katana ZERO Archipelago client.

Maps GameMaker room identifiers and in-game progression triggers to
Archipelago Location IDs.
"""

from typing import Dict, List, NamedTuple, Optional

BASE_LOCATION_ID = 82200000


class CheckTrigger(NamedTuple):
    location_id: int
    name: str
    target_room: str
    stage_clear: bool = False
    boss_defeat: bool = False
    milestone: bool = False
    key_pickup: bool = False


# All 40 Katana ZERO Archipelago checks
CHECK_DEFINITIONS: List[CheckTrigger] = [
    # ── Stage Clears (11) ──────────────────────────────────────────────────
    CheckTrigger(BASE_LOCATION_ID + 0,  "Factory - Tape Completed",        "room_factory_4",          stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 1,  "Hotel - Tape Completed",          "room_motel_7",            stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 2,  "Club - Tape Completed",           "room_club_7",             stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 3,  "Prison - Tape Completed",         "room_prison_5",           stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 3,  "Prison - Tape Completed",         "room_prison_0_return",    stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 4,  "Studio 51 - Tape Completed",      "room_haunted_finale2",    stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 5,  "Mansion - Tape Completed",        "room_mansion_bikechase",  stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 6,  "Chinatown - Tape Completed",      "room_chinatown_10",       stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 7,  "Dragon - Tape Completed",         "room_dragon_end",         stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 8,  "Slaughterhouse - Tape Completed", "room_factory2_end",       stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 9,  "Bunker - Tape Completed",         "room_bunker2_end",        stage_clear=True),
    CheckTrigger(BASE_LOCATION_ID + 10, "Government Lab - Tape Completed", "room_government_0",       stage_clear=True),

    # ── Mid-Stage Milestones (20) ──────────────────────────────────────────
    CheckTrigger(BASE_LOCATION_ID + 11, "Factory - Upper Floors Cleared",       "room_factory_2",          milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 12, "Factory - Rooftop Reached",            "room_factory_3",          milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 13, "Hotel - Lobby Cleared",                "room_motel_2",            milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 14, "Hotel - Penthouse Reached",            "room_motel_6",            milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 15, "Club - Dance Floor Cleared",           "room_club_3",             milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 16, "Club - VIP Lounge Reached",            "room_club_5",             milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 17, "Prison - Cell Block Cleared",          "room_prison_2",           milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 18, "Prison - Warden Office Reached",       "room_prison_4",           milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 19, "Studio 51 - Quiet Hills Set Cleared",  "room_haunted_silent2",    milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 20, "Studio 51 - Backstage Reached",        "room_haunted_hub_return", milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 21, "Mansion - Ground Floor Cleared",       "room_mansion_2",          milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 22, "Mansion - Attic Reached",              "room_mansion_4",          milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 23, "Chinatown - Market Cleared",           "room_chinatown_4",        milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 24, "Chinatown - Rooftops Reached",         "room_chinatown_8",        milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 25, "Dragon - Street Level Cleared",        "room_dragon_4",           milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 26, "Dragon - Dragon's Den Reached",        "room_dragon_8",           milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 27, "Slaughterhouse - Entry Cleared",       "room_factory2_3",         milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 28, "Slaughterhouse - Camera Room Reached", "room_factory2_7",         milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 29, "Bunker - Exterior Cleared",            "room_bunker_1",           milestone=True),
    CheckTrigger(BASE_LOCATION_ID + 30, "Bunker - Deep Bunker Reached",         "room_bunker_6",           milestone=True),

    # ── Boss Defeats (4) ───────────────────────────────────────────────────
    CheckTrigger(BASE_LOCATION_ID + 31, "V Defeated",            "room_haunted_finale2",    boss_defeat=True),
    CheckTrigger(BASE_LOCATION_ID + 32, "Kissyface Defeated",    "room_factory2_9",         boss_defeat=True),
    CheckTrigger(BASE_LOCATION_ID + 33, "Headhunter Defeated",   "room_bunker2_boss_final", boss_defeat=True),
    CheckTrigger(BASE_LOCATION_ID + 34, "Psychiatrist Defeated", "room_psychiatrist_nightmare", boss_defeat=True),

    # ── Vanilla Hidden Key Spots (5) ───────────────────────────────────────
    CheckTrigger(BASE_LOCATION_ID + 35, "Factory - Left Roof Corpse",        "room_factory_secretend", key_pickup=True),
    CheckTrigger(BASE_LOCATION_ID + 36, "Hotel - Penthouse Assassination",   "room_motel_7",           key_pickup=True),
    CheckTrigger(BASE_LOCATION_ID + 37, "Prison - Pacifist Suitcase",        "room_prison_sewer_1",    key_pickup=True),
    CheckTrigger(BASE_LOCATION_ID + 38, "Mansion - Robber's Sack",           "room_mansion_4",         key_pickup=True),
    CheckTrigger(BASE_LOCATION_ID + 39, "Slaughterhouse - Camera Room",      "room_factory2_7",        key_pickup=True),
]

# Fast lookup from location_id -> CheckTrigger
LOCATION_BY_ID: Dict[int, CheckTrigger] = {c.location_id: c for c in CHECK_DEFINITIONS}

# Fast lookup from target_room -> List of CheckTriggers in that room
CHECKS_BY_ROOM: Dict[str, List[CheckTrigger]] = {}
for c in CHECK_DEFINITIONS:
    CHECKS_BY_ROOM.setdefault(c.target_room, []).append(c)
