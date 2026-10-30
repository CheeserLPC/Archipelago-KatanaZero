"""Item definitions for Katana ZERO Archipelago world."""

from typing import Dict, List, NamedTuple, Optional

from BaseClasses import Item, ItemClassification


class KatanaZeroItem(Item):
    """Represents an item in the Katana ZERO game world."""
    game = "Katana ZERO"


class ItemData(NamedTuple):
    """Data class for item definitions.

    Attributes:
        code: The unique numeric ID for this item, or None for events.
        classification: The Archipelago item classification.
        count: The base number of this item to place in the item pool.
    """
    code: Optional[int]
    classification: ItemClassification
    count: int


# Base item ID for Katana ZERO (range: 82100000 – 82100099)
BASE_ITEM_ID = 82100000

item_table: Dict[str, ItemData] = {
    # ── VHS Tapes (progression) ── IDs 82100000-82100010
    "Tape: Factory":        ItemData(BASE_ITEM_ID + 0,  ItemClassification.progression, 1),
    "Tape: Hotel":          ItemData(BASE_ITEM_ID + 1,  ItemClassification.progression, 1),
    "Tape: Club":           ItemData(BASE_ITEM_ID + 2,  ItemClassification.progression, 1),
    "Tape: Prison":         ItemData(BASE_ITEM_ID + 3,  ItemClassification.progression, 1),
    "Tape: Studio 51":      ItemData(BASE_ITEM_ID + 4,  ItemClassification.progression, 1),
    "Tape: Mansion":        ItemData(BASE_ITEM_ID + 5,  ItemClassification.progression, 1),
    "Tape: Chinatown":      ItemData(BASE_ITEM_ID + 6,  ItemClassification.progression, 1),
    "Tape: Dragon":         ItemData(BASE_ITEM_ID + 7,  ItemClassification.progression, 1),
    "Tape: Slaughterhouse": ItemData(BASE_ITEM_ID + 8,  ItemClassification.progression, 1),
    "Tape: Bunker":         ItemData(BASE_ITEM_ID + 9,  ItemClassification.progression, 1),
    "Tape: Government Lab": ItemData(BASE_ITEM_ID + 10, ItemClassification.progression, 1),

    # ── Mechanic Shards (progression) ── IDs 82100011-82100015
    "Chronos":              ItemData(BASE_ITEM_ID + 11, ItemClassification.progression, 1),
    "Wall Jump":            ItemData(BASE_ITEM_ID + 13, ItemClassification.progression, 1),
    "Deflect":              ItemData(BASE_ITEM_ID + 14, ItemClassification.progression, 1),
    "Strength Training":    ItemData(BASE_ITEM_ID + 15, ItemClassification.progression, 1),

    # ── Government Lab Keys (progression) ── IDs 82100016-82100020
    "Prism Key":            ItemData(BASE_ITEM_ID + 16, ItemClassification.progression, 1),
    "Master Key":           ItemData(BASE_ITEM_ID + 17, ItemClassification.progression, 1),
    "Prototype Key":        ItemData(BASE_ITEM_ID + 18, ItemClassification.progression, 1),
    "Phoenix Key":          ItemData(BASE_ITEM_ID + 19, ItemClassification.progression, 1),
    "Savant Key":           ItemData(BASE_ITEM_ID + 20, ItemClassification.progression, 1),

    # ── Swords (useful) ── IDs 82100021-82100025
    "Prism Sword":          ItemData(BASE_ITEM_ID + 21, ItemClassification.useful, 1),
    "Sword of Masters":     ItemData(BASE_ITEM_ID + 22, ItemClassification.useful, 1),
    "Claymore Prototype":   ItemData(BASE_ITEM_ID + 23, ItemClassification.useful, 1),
    "Phoenix Edge":         ItemData(BASE_ITEM_ID + 24, ItemClassification.useful, 1),
    "Savant Knife":         ItemData(BASE_ITEM_ID + 25, ItemClassification.useful, 1),

    # ── Traps ── IDs 82100026-82100030, 82100034
    # Inverts player controls for 15 seconds or until death.
    "Chronos Overdose":     ItemData(BASE_ITEM_ID + 26, ItemClassification.trap, 1),
    # Temporarily freezes the player in place for 15 seconds or until death.
    "Freeze Trap":          ItemData(BASE_ITEM_ID + 27, ItemClassification.trap, 1),
    # Disables slow-mo ability for 15 seconds or until death.
    "Chronos Disruptor":    ItemData(BASE_ITEM_ID + 28, ItemClassification.trap, 1),
    # Flips the entire screen upside-down for 15 seconds or until death.
    "Screen Flip":          ItemData(BASE_ITEM_ID + 29, ItemClassification.trap, 1),
    # Teleports player to random position in current room.
    "Spatial Warp":         ItemData(BASE_ITEM_ID + 30, ItemClassification.trap, 1),
    # Disables dodge roll for 15 seconds or until death.
    "Roll Disruptor":       ItemData(BASE_ITEM_ID + 34, ItemClassification.trap, 1),
    # Disables attack button (sword slash) for 5 seconds or until death.
    "Pacifist Trap":        ItemData(BASE_ITEM_ID + 35, ItemClassification.trap, 1),

    # ── Filler ── IDs 82100031-82100033
    "Chronos Dose":         ItemData(BASE_ITEM_ID + 31, ItemClassification.filler, 1),
    "Herbal Tea":           ItemData(BASE_ITEM_ID + 32, ItemClassification.filler, 1),
    "Dossier":              ItemData(BASE_ITEM_ID + 33, ItemClassification.filler, 1),
}

# Reverse lookup: item name → numeric ID (excludes event items with code=None).
item_name_to_id: Dict[str, int] = {
    name: data.code for name, data in item_table.items() if data.code is not None
}


def get_filler_item_names() -> List[str]:
    """Return the names of all filler-classified items."""
    return [name for name, data in item_table.items()
            if data.classification == ItemClassification.filler]


def get_trap_item_names() -> List[str]:
    """Return the names of all trap-classified items."""
    return [name for name, data in item_table.items()
            if data.classification == ItemClassification.trap]
