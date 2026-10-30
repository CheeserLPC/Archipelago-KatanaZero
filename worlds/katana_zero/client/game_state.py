"""Game State and Logic Coordinator for Katana ZERO.

Monitors room transitions, location check completions, player mortality,
and applies mechanic restrictions & active trap modifiers in real-time.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, List, Optional, Set

from .death_link_handler import DeathLinkHandler
from .enemy_data import ENEMY_BY_IID
from .item_manager import ItemManager
from .memory_reader import KatanaMemory
from .room_data import ROOM_ID_TO_NAME
from .room_mappings import BASE_LOCATION_ID, CHECKS_BY_ROOM, CheckTrigger
from .trap_manager import TrapManager

logger = logging.getLogger("KatanaZeroClient.GameState")

# Stage reach progression: if you reach a later stage, earlier stages are implicitly cleared
STAGE_REACH_IMPLICATIONS: Dict[str, List[int]] = {
    # Reaching Hotel proves Factory clear (Tape Completed: 82200000)
    "room_motel_": [BASE_LOCATION_ID + 0],
    # Reaching Club proves Hotel clear (82200001)
    "room_club_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1],
    # Reaching Prison proves Club clear (82200002)
    "room_prison_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2],
    # Reaching Studio proves Prison clear (82200003)
    "room_haunted_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3],
    # Reaching Mansion proves Studio clear (82200004)
    "room_mansion_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3, BASE_LOCATION_ID + 4],
    # Reaching Chinatown proves Mansion clear (82200005)
    "room_chinatown_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3, BASE_LOCATION_ID + 4, BASE_LOCATION_ID + 5],
    # Reaching Dragon proves Chinatown clear (82200006)
    "room_dragon_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3, BASE_LOCATION_ID + 4, BASE_LOCATION_ID + 5, BASE_LOCATION_ID + 6],
    # Reaching Slaughterhouse proves Dragon clear (82200007)
    "room_factory2_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3, BASE_LOCATION_ID + 4, BASE_LOCATION_ID + 5, BASE_LOCATION_ID + 6, BASE_LOCATION_ID + 7],
    # Reaching Bunker proves Slaughterhouse clear (82200008)
    "room_bunker_": [BASE_LOCATION_ID + 0, BASE_LOCATION_ID + 1, BASE_LOCATION_ID + 2, BASE_LOCATION_ID + 3, BASE_LOCATION_ID + 4, BASE_LOCATION_ID + 5, BASE_LOCATION_ID + 6, BASE_LOCATION_ID + 7, BASE_LOCATION_ID + 8],
}


class GameStateTracker:
    """Tracks active game state, room transitions, and location checks."""

    def __init__(
        self,
        memory: KatanaMemory,
        item_manager: ItemManager,
        death_link: DeathLinkHandler,
        trap_manager: TrapManager,
        send_check_callback: Optional[Callable[[List[int]], None]] = None,
    ) -> None:
        self.mem = memory
        self.items = item_manager
        self.death_link = death_link
        self.traps = trap_manager
        self.send_checks = send_check_callback

        # Wire gameplay check into TrapManager for safe trap dispatch
        if self.traps:
            self.traps.is_gameplay_active_fn = self.is_in_combat_gameplay

        # Tracking state
        self.current_room: str = ""
        self.previous_room: str = ""
        self.room_entered_time: float = time.time()
        self.checked_locations: Set[int] = set()
        self.missing_locations: Set[int] = set()
        self.last_death_count: int = 0
        self.visited_rooms_in_run: Set[str] = set()
        self.killed_enemy_iids: Set[int] = set()
        self.enemysanity_enabled: bool = False
        self.was_attached: bool = False

    def is_in_combat_gameplay(self) -> bool:
        """Return True only when player is confirmed in an active combat room and controllable."""
        if not self.mem.is_attached():
            return False

        room = self.current_room or ""
        if not room:
            return False

        # Non-combat or cutscene rooms
        non_combat = (
            "title", "menu", "levelselect", "ending", "apartment",
            "psychiatrist", "limo", "bar", "cutscene", "interrogation"
        )
        if any(nc in room.lower() for nc in non_combat):
            return False

        # Must have a valid combat stage prefix
        combat_prefixes = (
            "room_factory", "room_motel", "room_club", "room_prison",
            "room_studio", "room_mansion", "room_chinatown", "room_dragon",
            "room_slaughterhouse", "room_bunker", "room_lab", "room_government"
        )
        if not any(room.startswith(p) for p in combat_prefixes):
            return False

        # Allow at least 0.8s for room instances to fully initialize after entering
        if time.time() - self.room_entered_time < 0.8:
            return False

        # Player instance must exist, strictly match obj_player, and have valid coords
        p_inst = self.mem.get_player_instance()
        if not p_inst:
            return False

        pos = self.mem.get_player_position()
        if not pos or pos[0] <= 0 or pos[1] <= 0:
            return False

        return True

    def set_location_info(self, checked: Set[int], missing: Set[int]) -> None:
        """Initialize location check knowledge from Archipelago connection."""
        self.checked_locations = set(checked)
        self.missing_locations = set(missing)
        for loc in (checked | missing):
            if loc >= 82200100:
                self.enemysanity_enabled = True
                break
        logger.info(
            f"Location state synced: {len(self.checked_locations)} checked, {len(self.missing_locations)} remaining (Enemysanity: {self.enemysanity_enabled})"
        )
        # Evaluate current room immediately if already in game
        if self.current_room:
            self._evaluate_location_checks(self.current_room)

    def on_room_changed(self, new_room: str) -> None:
        """Handle player moving to a new GameMaker room."""
        if not new_room or new_room == self.current_room:
            return

        self.previous_room = self.current_room
        self.current_room = new_room
        self.room_entered_time = time.time()
        self.visited_rooms_in_run.add(new_room)

        logger.info(f"[ROOM TRANSITION] {self.previous_room or 'Start'} -> {self.current_room}")

        # Check for location triggers in the new room
        self._evaluate_location_checks(new_room)

    def _evaluate_location_checks(self, room: str) -> None:
        """Evaluate if any new Archipelago checks were completed."""
        new_checks: List[int] = []

        # 1. Direct room checks from room_mappings
        triggers = CHECKS_BY_ROOM.get(room, [])
        for trig in triggers:
            loc_id = trig.location_id
            if loc_id not in self.checked_locations:
                if trig.milestone or trig.stage_clear:
                    new_checks.append(loc_id)
                    self.checked_locations.add(loc_id)
                    logger.info(f"[CHECK COMPLETED] {trig.name} (ID: {loc_id})")

        # 2. Implicit earlier stage clears based on chapter reached
        for prefix, implied_locs in STAGE_REACH_IMPLICATIONS.items():
            if room.startswith(prefix):
                for loc_id in implied_locs:
                    if loc_id not in self.checked_locations:
                        new_checks.append(loc_id)
                        self.checked_locations.add(loc_id)
                        logger.info(f"[STAGE CLEAR VERIFIED] Check ID {loc_id} (reached {room})")

        if new_checks and self.send_checks:
            self.send_checks(new_checks)

    def trigger_boss_defeated(self, boss_location_name: str) -> None:
        """Called when a boss defeat event occurs."""
        for trig in CHECKS_BY_ROOM.get(self.current_room, []):
            if trig.boss_defeat and trig.name == boss_location_name:
                loc_id = trig.location_id
                if loc_id not in self.checked_locations:
                    self.checked_locations.add(loc_id)
                    logger.info(f"[BOSS CHECK COMPLETED] {trig.name} (ID: {loc_id})")
                    if self.send_checks:
                        self.send_checks([loc_id])

    def trigger_key_pickup(self, key_location_name: str) -> None:
        """Called when a vanilla key check is picked up."""
        for trig in CHECKS_BY_ROOM.get(self.current_room, []):
            if trig.key_pickup and trig.name == key_location_name:
                loc_id = trig.location_id
                if loc_id not in self.checked_locations:
                    self.checked_locations.add(loc_id)
                    logger.info(f"[KEY CHECK COMPLETED] {trig.name} (ID: {loc_id})")
                    if self.send_checks:
                        self.send_checks([loc_id])

    def on_player_died(self) -> None:
        """Called when player death is confirmed in the running game."""
        self.death_link.on_local_player_died()
        self.traps.clear_all()

    def kill_player_in_game(self) -> None:
        """Execute instant kill on player in Katana ZERO."""
        logger.warning("Executing in-game player death (DeathLink / Forced Kill)")
        self.mem.kill_player_remote()

    def update(self) -> None:
        """Periodic tick called by main client loop (~10 Hz)."""
        # Update active trap countdowns
        self.traps.update()

        # Check attachment status
        if not self.mem.is_attached():
            if self.was_attached:
                self.was_attached = False
                logger.warning("=" * 65)
                logger.warning("[CONNECTION LOST] Lost connection to Katana ZERO.exe!")
                logger.warning("[CONNECTION LOST] Process terminated or closed.")
                logger.warning("[CONNECTION LOST] Waiting for Katana ZERO to restart...")
                logger.warning("=" * 65)

            if not self.mem.attach():
                return

            # Successfully attached just now
            self.was_attached = True
            logger.info("=" * 65)
            logger.info(f"[GAME HOOK SUCCESS] Successfully hooked to Katana ZERO.exe!")
            logger.info(f"[GAME HOOK SUCCESS] PID: {self.mem.pid} | Base Address: 0x{self.mem.base_address:08X}")
            logger.info("[GAME HOOK SUCCESS] Memory reader, death hooks, and enemy tracking are active!")
            logger.info("=" * 65)
            self.last_death_count = self.mem.read_death_count()
        else:
            if not self.was_attached:
                self.was_attached = True
                logger.info("=" * 65)
                logger.info(f"[GAME HOOK SUCCESS] Successfully hooked to Katana ZERO.exe!")
                logger.info(f"[GAME HOOK SUCCESS] PID: {self.mem.pid} | Base Address: 0x{self.mem.base_address:08X}")
                logger.info("[GAME HOOK SUCCESS] Memory reader, death hooks, and enemy tracking are active!")
                logger.info("=" * 65)
                self.last_death_count = self.mem.read_death_count()

        # 1. Poll Room Transitions
        room_id = self.mem.read_current_room_id()
        if room_id is not None and room_id in ROOM_ID_TO_NAME:
            room_name = ROOM_ID_TO_NAME[room_id]
            if room_name != self.current_room:
                self.on_room_changed(room_name)

        # 2. Poll DeathLink In-Game Deaths
        cur_deaths = self.mem.read_death_count()
        if cur_deaths > self.last_death_count:
            death_diff = cur_deaths - self.last_death_count
            self.last_death_count = cur_deaths
            for _ in range(death_diff):
                self.on_player_died()

        # 3. Enforce Mechanic Locks/Unlocks in memory
        for mech_name in ["Chronos", "Dodge Roll", "Wall Jump", "Deflect", "Item Throw"]:
            is_unlocked = self.items.mechanics.get(mech_name, False)
            if mech_name == "Chronos" and self.traps.is_slowmo_disabled():
                is_unlocked = False
            self.mem.set_mechanic_state(mech_name, is_unlocked)

        # 4. Poll Killed Enemy Checks (Enemysanity)
        if self.enemysanity_enabled:
            new_iids = self.mem.read_killed_enemy_ids()
            if new_iids:
                enemy_checks: List[int] = []
                for iid in new_iids:
                    if iid not in self.killed_enemy_iids:
                        self.killed_enemy_iids.add(iid)
                        enemy = ENEMY_BY_IID.get(iid)
                        if enemy:
                            loc_id = enemy.location_id
                            if loc_id not in self.checked_locations:
                                self.checked_locations.add(loc_id)
                                enemy_checks.append(loc_id)
                                logger.info(
                                    f"[ENEMY CHECK COMPLETED] {enemy.name} (Location ID: {loc_id}, IID: {iid})"
                                )
                if enemy_checks and self.send_checks:
                    self.send_checks(enemy_checks)
