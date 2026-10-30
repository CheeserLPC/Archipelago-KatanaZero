"""DeathLink handler for Katana ZERO Archipelago client.

Features:
- Instant kill on current screen when incoming DeathLink arrives
- DeathLink Amnesty counter: allows multiple deaths to accumulate before broadcasting
- Prevents infinite death feedback loops
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable, Optional

logger = logging.getLogger("KatanaZeroClient.DeathLink")

KATANA_ZERO_DEATH_MESSAGES = [
    "ran out of Chronos.",
    "suffered a fatal lapse in precognition.",
    "failed to deflect the incoming bullet.",
    "hesitated and was cut down.",
    "forgot to dodge roll.",
    "let the rewind timer expire.",
    "failed the psychiatric evaluation.",
    "missed their daily dose of medicine.",
    "brought a katana to an automatic rifle fight.",
    "tried to deflect shotgun buckshot with a sword.",
    "suffered from severe Chronos withdrawal.",
    "stepped into a laser tripwire.",
    "rewound time one too many times.",
    "failed to eliminate all targets.",
    "was terminated by a fellow NULL soldier.",
    "was caught off guard by a ceiling turret.",
    "didn't answer the phone in time.",
    "lost their focus in the replay.",
    "was tackled by a riot shield cop.",
    "cut through the wrong door.",
]


class DeathLinkHandler:
    """Manages DeathLink signals, amnesty counters, and trigger callbacks."""

    def __init__(
        self,
        player_name: str,
        enabled: bool = False,
        amnesty: int = 0,
        send_bounce_callback: Optional[Callable[[dict], None]] = None,
        kill_player_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        self.player_name = player_name
        self.enabled = enabled
        self.amnesty_limit = amnesty  # 0 = send immediately
        self.current_deaths = 0       # Accumulated deaths
        self.total_deaths = 0         # Lifetime deaths session
        self.last_death_time: float = 0.0
        self.last_incoming_time: float = 0.0
        self.send_bounce = send_bounce_callback
        self.kill_player = kill_player_callback

    def set_config(self, enabled: bool, amnesty: int) -> None:
        """Update settings received from slot data."""
        self.enabled = enabled
        self.amnesty_limit = max(0, amnesty)
        logger.info(f"DeathLink config updated: enabled={self.enabled}, amnesty={self.amnesty_limit}")

    def on_local_player_died(self, cause: Optional[str] = None) -> bool:
        """Called when the local player dies in Katana ZERO.

        Returns True if a DeathLink was broadcast to other players.
        """
        if not self.enabled:
            return False

        now = time.time()
        # Cooldown protection: ignore deaths occurring within 1.5s of an incoming DeathLink
        if now - self.last_incoming_time < 1.5:
            logger.debug("Ignoring local death triggered by incoming DeathLink")
            return False

        # Debounce multiple deaths occurring in quick succession (<1s)
        if now - self.last_death_time < 1.0:
            return False

        self.last_death_time = now
        self.total_deaths += 1
        self.current_deaths += 1

        logger.info(
            f"Local death #{self.total_deaths} recorded (Accumulated: {self.current_deaths}/{self.amnesty_limit})"
        )

        # Check amnesty
        if self.current_deaths > self.amnesty_limit:
            self.current_deaths = 0

            # Generate flavored death message
            if not cause:
                action = random.choice(KATANA_ZERO_DEATH_MESSAGES)
                formatted_cause = f"{self.player_name} {action}"
            elif cause.startswith(self.player_name):
                formatted_cause = cause if cause.endswith(".") else f"{cause}."
            else:
                stripped = cause.rstrip(".")
                formatted_cause = f"{self.player_name} {stripped}."

            if self.send_bounce:
                payload = {
                    "time": now,
                    "source": self.player_name,
                    "cause": formatted_cause,
                }
                logger.warning(f"[DEATHLINK BROADCAST] Sending death to multiworld: {payload['cause']}")
                self.send_bounce(payload)
                return True
        else:
            remaining = self.amnesty_limit - self.current_deaths + 1
            logger.info(f"DeathLink amnesty absorbed death ({remaining} remaining before broadcast)")

        return False

    def on_incoming_deathlink(self, data: dict) -> bool:
        """Called when a DeathLink packet is received from the server.

        Returns True if the player was killed.
        """
        if not self.enabled:
            return False

        source = data.get("source", "Unknown")
        cause = data.get("cause", f"{source} died.")
        death_time = data.get("time", time.time())

        # Avoid echo from ourselves
        if source == self.player_name:
            return False

        logger.warning(f"[DeathLink Received] {cause}")
        self.last_incoming_time = time.time()

        if self.kill_player:
            self.kill_player()
            return True

        return False
