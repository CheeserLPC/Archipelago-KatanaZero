"""Trap manager for Katana ZERO Archipelago client.

Handles execution and duration tracking for:
- Chronos Overdose (inverts controls)
- Freeze Trap (freezes player)
- Chronos Disruptor (disables slow-mo)
- Screen Flip (flips screen orientation)
- Spatial Warp (random room teleport)
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, Dict, Optional

logger = logging.getLogger("KatanaZeroClient.Traps")

# Trap item IDs (matching Items.py)
TRAP_CHRONOS_OVERDOSE = 82100026
TRAP_FREEZE = 82100027
TRAP_CHRONOS_DISRUPTOR = 82100028
TRAP_SCREEN_FLIP = 82100029
TRAP_SPATIAL_WARP = 82100030
TRAP_ROLL_DISRUPTOR = 82100034
TRAP_PACIFIST = 82100035

TRAP_DURATIONS: Dict[int, float] = {
    TRAP_CHRONOS_OVERDOSE: 15.0,    # 15 seconds of inverted controls (or until death)
    TRAP_FREEZE: 3.0,               # 3 seconds frozen in place (or until death)
    TRAP_CHRONOS_DISRUPTOR: 15.0,  # 15 seconds of no slow-mo (or until death)
    TRAP_SCREEN_FLIP: 15.0,        # 15 seconds screen flipped (or until death)
    TRAP_ROLL_DISRUPTOR: 15.0,     # 15 seconds of no dodge roll (or until death)
    TRAP_PACIFIST: 5.0,            # 5 seconds of attack disabled (or until death)
    TRAP_SPATIAL_WARP: 0.1,        # Instantaneous teleport
}


class TrapManager:
    """Coordinates active trap statuses, pending trap queue, and expiry timers."""

    def __init__(
        self,
        set_controls_inverted: Optional[Callable[[bool], None]] = None,
        set_player_frozen: Optional[Callable[[bool], None]] = None,
        set_slowmo_disabled: Optional[Callable[[bool], None]] = None,
        set_screen_flipped: Optional[Callable[[bool], None]] = None,
        teleport_player: Optional[Callable[[], None]] = None,
        set_roll_disabled: Optional[Callable[[bool], None]] = None,
        set_attack_disabled: Optional[Callable[[bool], None]] = None,
        is_gameplay_active_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.set_controls_inverted = set_controls_inverted
        self.set_player_frozen = set_player_frozen
        self.set_slowmo_disabled = set_slowmo_disabled
        self.set_screen_flipped = set_screen_flipped
        self.teleport_player = teleport_player
        self.set_roll_disabled = set_roll_disabled
        self.set_attack_disabled = set_attack_disabled
        self.is_gameplay_active_fn = is_gameplay_active_fn

        # Active trap expiration timestamps (item_id -> expire_timestamp)
        self.active_traps: Dict[int, float] = {}
        # Pending queue for traps received during transitions, cutscenes, or menus
        self.pending_traps: List[tuple[int, str]] = []
        self.last_trap_trigger_time: float = 0.0

    def trigger_trap(self, item_id: int, item_name: str) -> None:
        """Enqueue or immediately execute a trap depending on gameplay state."""
        # If gameplay is not confirmed active, safely queue the trap
        if self.is_gameplay_active_fn and not self.is_gameplay_active_fn():
            self.pending_traps.append((item_id, item_name))
            logger.info(f"[TRAP QUEUED] {item_name} queued (waiting for active combat room, {len(self.pending_traps)} pending)")
            return

        self._execute_trap(item_id, item_name)

    def _execute_trap(self, item_id: int, item_name: str) -> None:
        """Directly trigger in-game trap effect and set expiration timer."""
        duration = TRAP_DURATIONS.get(item_id, 5.0)
        now = time.time()
        expire = now + duration
        self.last_trap_trigger_time = now

        logger.warning(f"[TRAP TRIGGERED] {item_name} (Duration: {duration:.1f}s)")

        if item_id == TRAP_CHRONOS_OVERDOSE:
            self.active_traps[item_id] = expire
            if self.set_controls_inverted:
                self.set_controls_inverted(True)

        elif item_id == TRAP_FREEZE:
            self.active_traps[item_id] = expire
            if self.set_player_frozen:
                self.set_player_frozen(True)

        elif item_id == TRAP_CHRONOS_DISRUPTOR:
            self.active_traps[item_id] = expire
            if self.set_slowmo_disabled:
                self.set_slowmo_disabled(True)

        elif item_id == TRAP_SCREEN_FLIP:
            self.active_traps[item_id] = expire
            if self.set_screen_flipped:
                self.set_screen_flipped(True)

        elif item_id == TRAP_ROLL_DISRUPTOR:
            self.active_traps[item_id] = expire
            if self.set_roll_disabled:
                self.set_roll_disabled(True)

        elif item_id == TRAP_PACIFIST:
            self.active_traps[item_id] = expire
            if self.set_attack_disabled:
                self.set_attack_disabled(True)

        elif item_id == TRAP_SPATIAL_WARP:
            if self.teleport_player:
                self.teleport_player()

    def update(self) -> None:
        """Check active traps and clear expired effects, then dispatch queued traps."""
        now = time.time()
        expired = [item_id for item_id, exp in self.active_traps.items() if now >= exp]

        for item_id in expired:
            del self.active_traps[item_id]

            if item_id == TRAP_CHRONOS_OVERDOSE:
                logger.info("Chronos Overdose effect expired. Controls restored.")
                if self.set_controls_inverted:
                    self.set_controls_inverted(False)

            elif item_id == TRAP_FREEZE:
                logger.info("Freeze Trap expired. Player unfrozen.")
                if self.set_player_frozen:
                    self.set_player_frozen(False)

            elif item_id == TRAP_CHRONOS_DISRUPTOR:
                logger.info("Chronos Disruptor expired. Slow-mo restored.")
                if self.set_slowmo_disabled:
                    self.set_slowmo_disabled(False)

            elif item_id == TRAP_SCREEN_FLIP:
                logger.info("Screen Flip expired. Screen orientation restored.")
                if self.set_screen_flipped:
                    self.set_screen_flipped(False)

            elif item_id == TRAP_ROLL_DISRUPTOR:
                logger.info("Roll Disruptor expired. Dodge roll restored.")
                if self.set_roll_disabled:
                    self.set_roll_disabled(False)

            elif item_id == TRAP_PACIFIST:
                logger.info("Pacifist Trap expired. Attack restored.")
                if self.set_attack_disabled:
                    self.set_attack_disabled(False)

        # Process pending queued traps if gameplay is active and spaced apart
        if self.pending_traps and (now - self.last_trap_trigger_time >= 1.5):
            if not self.is_gameplay_active_fn or self.is_gameplay_active_fn():
                item_id, item_name = self.pending_traps.pop(0)
                self._execute_trap(item_id, item_name)

    def is_slowmo_disabled(self) -> bool:
        """Check if Chronos Disruptor trap is currently active."""
        return TRAP_CHRONOS_DISRUPTOR in self.active_traps

    def is_roll_disabled(self) -> bool:
        """Check if Roll Disruptor trap is currently active."""
        return TRAP_ROLL_DISRUPTOR in self.active_traps

    def is_attack_disabled(self) -> bool:
        """Check if Pacifist Trap is currently active."""
        return TRAP_PACIFIST in self.active_traps

    def clear_all(self) -> None:
        """Instantly clear all active traps (e.g., on death)."""
        if TRAP_CHRONOS_OVERDOSE in self.active_traps and self.set_controls_inverted:
            self.set_controls_inverted(False)
        if TRAP_FREEZE in self.active_traps and self.set_player_frozen:
            self.set_player_frozen(False)
        if TRAP_CHRONOS_DISRUPTOR in self.active_traps and self.set_slowmo_disabled:
            self.set_slowmo_disabled(False)
        if TRAP_SCREEN_FLIP in self.active_traps and self.set_screen_flipped:
            self.set_screen_flipped(False)
        if TRAP_ROLL_DISRUPTOR in self.active_traps and self.set_roll_disabled:
            self.set_roll_disabled(False)
        if TRAP_PACIFIST in self.active_traps and self.set_attack_disabled:
            self.set_attack_disabled(False)
        self.active_traps.clear()
