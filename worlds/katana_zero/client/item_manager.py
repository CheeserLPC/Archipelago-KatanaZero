"""Item Manager for Katana ZERO Archipelago client.

Tracks inventory state (Tapes, Mechanics, Keys, Swords) and notifies
game state / memory controller when items change.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger("KatanaZeroClient.Items")

BASE_ITEM_ID = 82100000

# Item ID definitions
ITEM_NAMES: Dict[int, str] = {
    # Tapes
    BASE_ITEM_ID + 0:  "Tape: Factory",
    BASE_ITEM_ID + 1:  "Tape: Hotel",
    BASE_ITEM_ID + 2:  "Tape: Club",
    BASE_ITEM_ID + 3:  "Tape: Prison",
    BASE_ITEM_ID + 4:  "Tape: Studio 51",
    BASE_ITEM_ID + 5:  "Tape: Mansion",
    BASE_ITEM_ID + 6:  "Tape: Chinatown",
    BASE_ITEM_ID + 7:  "Tape: Dragon",
    BASE_ITEM_ID + 8:  "Tape: Slaughterhouse",
    BASE_ITEM_ID + 9:  "Tape: Bunker",
    BASE_ITEM_ID + 10: "Tape: Government Lab",
    # Mechanics
    BASE_ITEM_ID + 11: "Chronos",
    BASE_ITEM_ID + 12: "Dodge Roll",
    BASE_ITEM_ID + 13: "Wall Jump",
    BASE_ITEM_ID + 14: "Deflect",
    BASE_ITEM_ID + 15: "Item Throw",
    # Keys
    BASE_ITEM_ID + 16: "Prism Key",
    BASE_ITEM_ID + 17: "Master Key",
    BASE_ITEM_ID + 18: "Prototype Key",
    BASE_ITEM_ID + 19: "Phoenix Key",
    BASE_ITEM_ID + 20: "Savant Key",
    # Swords
    BASE_ITEM_ID + 21: "Prism Sword",
    BASE_ITEM_ID + 22: "Sword of Masters",
    BASE_ITEM_ID + 23: "Claymore Prototype",
    BASE_ITEM_ID + 24: "Phoenix Edge",
    BASE_ITEM_ID + 25: "Savant Knife",
    # Traps
    BASE_ITEM_ID + 26: "Chronos Overdose",
    BASE_ITEM_ID + 27: "Freeze Trap",
    BASE_ITEM_ID + 28: "Chronos Disruptor",
    BASE_ITEM_ID + 29: "Screen Flip",
    BASE_ITEM_ID + 30: "Spatial Warp",
    BASE_ITEM_ID + 34: "Roll Disruptor",
    BASE_ITEM_ID + 35: "Pacifist Trap",
    # Filler
    BASE_ITEM_ID + 31: "Chronos Dose",
    BASE_ITEM_ID + 32: "Herbal Tea",
    BASE_ITEM_ID + 33: "Dossier",
}


class ItemManager:
    """Manages player item collection state."""

    def __init__(self, trap_callback: Optional[Callable[[int, str], None]] = None) -> None:
        self.trap_callback = trap_callback
        self.received_items: List[int] = []
        self.collected_tapes: Set[str] = set()
        self.mechanics: Dict[str, bool] = {
            "Chronos": False,
            "Dodge Roll": True,
            "Wall Jump": True,
            "Deflect": True,
            "Item Throw": False,
        }
        self.keys: Set[str] = set()
        self.swords: Set[str] = set()

    def process_new_item(self, item_id: int) -> str:
        """Process an incoming item ID from Archipelago and update local state."""
        self.received_items.append(item_id)
        name = ITEM_NAMES.get(item_id, f"Unknown Item ({item_id})")

        # Tapes
        if BASE_ITEM_ID + 0 <= item_id <= BASE_ITEM_ID + 10:
            tape_name = name.replace("Tape: ", "")
            self.collected_tapes.add(tape_name)
            logger.info(f"[UNLOCKED TAPE] {tape_name} (Total Tapes: {len(self.collected_tapes)}/11)")

        # Mechanics
        elif BASE_ITEM_ID + 11 <= item_id <= BASE_ITEM_ID + 15:
            if name in self.mechanics:
                self.mechanics[name] = True
            logger.info(f"[UNLOCKED MECHANIC] {name}")

        # Keys
        elif BASE_ITEM_ID + 16 <= item_id <= BASE_ITEM_ID + 20:
            self.keys.add(name)
            logger.info(f"[UNLOCKED KEY] {name} (Keys: {len(self.keys)}/5)")

        # Swords
        elif BASE_ITEM_ID + 21 <= item_id <= BASE_ITEM_ID + 25:
            self.swords.add(name)
            logger.info(f"[UNLOCKED SWORD] {name}")

        # Traps
        elif (BASE_ITEM_ID + 26 <= item_id <= BASE_ITEM_ID + 30) or item_id in (BASE_ITEM_ID + 34, BASE_ITEM_ID + 35):
            logger.warning(f"[RECEIVED TRAP] {name} (Item ID: {item_id})")
            if self.trap_callback:
                self.trap_callback(item_id, name)
            else:
                logger.error(f"[TRAP ERROR] No trap callback configured! Cannot trigger {name}")

        # Filler
        elif BASE_ITEM_ID + 31 <= item_id <= BASE_ITEM_ID + 33:
            logger.info(f"[RECEIVED FILLER] {name}")

        return name

    def has_mechanic(self, mechanic_name: str) -> bool:
        """Query if a mechanic is unlocked."""
        return self.mechanics.get(mechanic_name, False)

    def has_tape(self, tape_name: str) -> bool:
        """Query if a stage tape is unlocked."""
        return tape_name in self.collected_tapes

    def has_key(self, key_name: str) -> bool:
        """Query if a lab key is unlocked."""
        return key_name in self.keys

    def tape_count(self) -> int:
        """Total number of unlocked tapes."""
        return len(self.collected_tapes)
