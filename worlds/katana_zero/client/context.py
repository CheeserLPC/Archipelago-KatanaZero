"""Katana ZERO Archipelago CommonContext Client.

Integrates with Archipelago's official CommonClient and Kivy GUI framework,
allowing the client to run seamlessly inside the Archipelago Launcher with a full GUI
or as an interactive command-line interface.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from CommonClient import (
    ClientCommandProcessor,
    CommonContext,
    gui_enabled,
    logger,
    server_loop,
)
from NetUtils import ClientStatus

from .death_link_handler import DeathLinkHandler
from .game_state import GameStateTracker
from .item_manager import ItemManager
from .memory_reader import KatanaMemory
from .room_mappings import CHECK_DEFINITIONS, LOCATION_BY_ID
from .save_manager import SaveManager
from .trap_manager import TrapManager


class KatanaZeroCommandProcessor(ClientCommandProcessor):
    """Console slash commands for Katana ZERO client."""

    ctx: KatanaZeroContext

    def _cmd_status(self) -> None:
        """Display game attachment and room state."""
        mem_ok = self.ctx.mem.is_attached()
        logger.info(f"Katana ZERO Memory: {'ATTACHED (PID: ' + str(self.ctx.mem.pid) + ')' if mem_ok else 'NOT RUNNING'}")
        logger.info(f"Current Room: {self.ctx.game_state.current_room or 'None'}")
        logger.info(f"Checks completed: {len(self.ctx.checked_locations)}/{len(self.ctx.missing_locations) + len(self.ctx.checked_locations)}")

    def _cmd_items(self) -> None:
        """List collected tapes, keys, and swords."""
        logger.info(f"Tapes ({len(self.ctx.item_mgr.collected_tapes)}/11): {sorted(self.ctx.item_mgr.collected_tapes)}")
        logger.info(f"Keys ({len(self.ctx.item_mgr.keys)}/5): {sorted(self.ctx.item_mgr.keys)}")
        logger.info(f"Swords ({len(self.ctx.item_mgr.swords)}/5): {sorted(self.ctx.item_mgr.swords)}")
        logger.info(f"Mechanics: {self.ctx.item_mgr.mechanics}")

    def _cmd_deathlink(self) -> None:
        """Display DeathLink and amnesty statistics."""
        dl = self.ctx.death_link_mgr
        logger.info(f"DeathLink Active: {dl.enabled}")
        logger.info(f"Amnesty Limit: {dl.amnesty_limit}")
        logger.info(f"Accumulated Deaths: {dl.current_deaths}")
        logger.info(f"Session Deaths: {dl.total_deaths}")

    def _cmd_sync(self) -> None:
        """Force save file synchronization to KatanaSave.zero."""
        ok = self.ctx.save_mgr.sync_unlocks(
            self.ctx.item_mgr.collected_tapes,
            self.ctx.item_mgr.keys,
            self.ctx.item_mgr.swords,
        )
        if ok:
            logger.info("KatanaSave.zero synchronized successfully.")
        else:
            logger.warning("Could not synchronize save file.")

    def _cmd_die(self) -> None:
        """Simulate a local death event for testing."""
        logger.info("Simulating local death...")
        self.ctx.game_state.on_player_died()

    def _cmd_test_incoming_death(self) -> None:
        """Simulate receiving an incoming DeathLink signal from another player."""
        logger.info("Simulating incoming DeathLink from peer...")
        self.ctx.death_link_mgr.on_incoming_deathlink(
            {"source": "PeerPlayer", "cause": "PeerPlayer met a tragic end."}
        )

    def _cmd_music(self, state: str = "") -> None:
        """Toggle or set Music Randomizer on/off."""
        if state.lower() in ("on", "1", "true"):
            new_val = True
        elif state.lower() in ("off", "0", "false"):
            new_val = False
        else:
            new_val = not self.ctx.mem.music_randomized
        self.ctx.mem.apply_audio_randomizer(
            randomize_music=new_val,
            randomize_sfx=self.ctx.mem.sfx_randomized,
            seed=self.ctx.mem.audio_seed or 42,
        )
        logger.info(f"Music Randomizer is now {'ENABLED' if new_val else 'DISABLED'}.")

    def _cmd_sfx(self, state: str = "") -> None:
        """Toggle or set Sound Effect Randomizer on/off."""
        if state.lower() in ("on", "1", "true"):
            new_val = True
        elif state.lower() in ("off", "0", "false"):
            new_val = False
        else:
            new_val = not self.ctx.mem.sfx_randomized
        self.ctx.mem.apply_audio_randomizer(
            randomize_music=self.ctx.mem.music_randomized,
            randomize_sfx=new_val,
            seed=self.ctx.mem.audio_seed or 42,
        )
        logger.info(f"SFX Randomizer is now {'ENABLED' if new_val else 'DISABLED'}.")

    def _cmd_audio(self) -> None:
        """Display audio randomizer status."""
        logger.info(
            f"Audio Randomizer Status: Music={'SHUFFLED' if self.ctx.mem.music_randomized else 'VANILLA'}, "
            f"SFX={'SHUFFLED' if self.ctx.mem.sfx_randomized else 'VANILLA'} (Hook Installed: {self.ctx.mem.audio_hook_installed})"
        )


def extract_item_id(item: Any) -> int:
    """Robustly extract integer item_id from NetworkItem, dict, list/tuple, or int."""
    if hasattr(item, "item"):
        return int(item.item)
    if isinstance(item, dict):
        return int(item.get("item", 0))
    if isinstance(item, (list, tuple)) and len(item) > 0:
        return int(item[0])
    return int(item)


class KatanaZeroContext(CommonContext):
    """Archipelago client context for Katana ZERO."""

    game = "Katana ZERO"
    command_processor = KatanaZeroCommandProcessor
    items_handling = 0b111  # Track local, non-local, and starting items

    def __init__(self, server_address: Optional[str] = None, password: Optional[str] = None) -> None:
        super().__init__(server_address, password)

        # Core systems
        self.mem = KatanaMemory()
        self.save_mgr = SaveManager()
        self.traps = TrapManager(
            set_controls_inverted=self._on_controls_inverted,
            set_player_frozen=self._on_player_frozen,
            set_slowmo_disabled=self._on_slowmo_disabled,
            set_screen_flipped=self._on_screen_flipped,
            teleport_player=self._on_teleport_player,
            set_roll_disabled=self._on_roll_disabled,
            set_attack_disabled=self._on_attack_disabled,
        )
        self.item_mgr = ItemManager(trap_callback=self.traps.trigger_trap)
        self.death_link_mgr = DeathLinkHandler(
            player_name=getattr(self, "auth", None) or "Zero",
            send_bounce_callback=self._send_deathlink_bounce,
            kill_player_callback=self._execute_kill_player,
        )
        self.game_state = GameStateTracker(
            memory=self.mem,
            item_manager=self.item_mgr,
            death_link=self.death_link_mgr,
            trap_manager=self.traps,
            send_check_callback=self._send_location_checks,
        )

        self.last_received_item_index: int = 0
        self.game_sync_task: Optional[asyncio.Task] = None

    # ── Trap Callbacks ────────────────────────────────────────────────────────

    def _on_controls_inverted(self, inverted: bool) -> None:
        state_str = "INVERTED" if inverted else "NORMAL"
        logger.warning(f"[TRAP] Controls status changed: {state_str}")
        self.mem.set_controls_inverted(inverted)

    def _on_player_frozen(self, frozen: bool) -> None:
        state_str = "FROZEN" if frozen else "UNFROZEN"
        logger.warning(f"[TRAP] Player movement status: {state_str}")
        self.mem.set_player_frozen(frozen)

    def _on_slowmo_disabled(self, disabled: bool) -> None:
        state_str = "DISABLED" if disabled else "ENABLED"
        logger.warning(f"[TRAP] Chronos slow-mo status: {state_str}")
        self.mem.set_slowmo_disabled(disabled)

    def _on_screen_flipped(self, flipped: bool) -> None:
        state_str = "FLIPPED" if flipped else "NORMAL"
        logger.warning(f"[TRAP] Screen orientation: {state_str}")
        self.mem.set_screen_flipped(flipped)

    def _on_teleport_player(self) -> None:
        logger.warning("[TRAP] Spatial Warp teleporting player safely to room spawn")
        self.mem.teleport_player()

    def _on_roll_disabled(self, disabled: bool) -> None:
        state_str = "DISABLED" if disabled else "ENABLED"
        logger.warning(f"[TRAP] Dodge roll status: {state_str}")
        self.mem.set_roll_disabled(disabled)

    def _on_attack_disabled(self, disabled: bool) -> None:
        state_str = "DISABLED" if disabled else "ENABLED"
        logger.warning(f"[TRAP] Pacifist Trap (attack status): {state_str}")
        self.mem.set_attack_disabled(disabled)

    def _send_deathlink_bounce(self, bounce_data: dict) -> None:
        """Broadcast DeathLink bounce via CommonContext."""
        cause = bounce_data.get("cause", "")
        if not cause:
            cause = f"{self.death_link_mgr.player_name} died in Katana ZERO."
        asyncio.create_task(self.send_death(cause))

    def _execute_kill_player(self) -> None:
        """Trigger player death in Katana ZERO."""
        self.game_state.kill_player_in_game()

    def _send_location_checks(self, location_ids: List[int]) -> None:
        """Send completed location checks to server."""
        asyncio.create_task(self.check_locations(location_ids))

    async def server_auth(self, password_requested: bool = False) -> None:
        """Perform initial server authentication."""
        if password_requested and not self.password:
            await super().server_auth(password_requested)
            return

        # Ensure DeathLink tag is included if enabled
        if "DeathLink" not in self.tags:
            self.tags.add("DeathLink")

        await self.get_username()
        await self.send_connect()

    def on_deathlink(self, data: dict) -> None:
        """Handle incoming DeathLink bounce from server."""
        super().on_deathlink(data)
        self.death_link_mgr.on_incoming_deathlink(data)

    def on_package(self, cmd: str, args: dict) -> None:
        """Handle incoming Archipelago protocol packets."""
        if cmd == "Connected":
            slot_data = args.get("slot_data", {})
            dl_enabled = bool(slot_data.get("death_link", 0))
            dl_amnesty = int(slot_data.get("death_link_amnesty", 0))

            player_name = self.auth
            if not player_name and hasattr(self, "player_names") and hasattr(self, "slot") and self.slot in self.player_names:
                player_name = self.player_names[self.slot]
            self.death_link_mgr.player_name = player_name or "Zero"
            self.death_link_mgr.set_config(enabled=dl_enabled, amnesty=dl_amnesty)
            self.game_state.set_location_info(self.checked_locations, self.missing_locations)
            if bool(slot_data.get("enemysanity", 0)):
                self.game_state.enemysanity_enabled = True

            rand_music = bool(slot_data.get("randomize_music", 0))
            rand_sfx = bool(slot_data.get("randomize_sfx", 0))
            audio_seed = slot_data.get("audio_seed", None)
            if audio_seed is None:
                audio_seed = getattr(self, "slot", 0) or 42

            self.mem.apply_audio_randomizer(
                randomize_music=rand_music,
                randomize_sfx=rand_sfx,
                seed=audio_seed,
            )

            logger.info("=" * 60)
            logger.info(f"Connected to Katana ZERO Multiworld as '{self.auth}'!")
            logger.info(f"Goal: {slot_data.get('goal', 'Government Lab')}")
            logger.info(f"Starting Tape: {slot_data.get('starting_tape', 'Factory')}")
            logger.info(f"Enemysanity: {'ENABLED' if self.game_state.enemysanity_enabled else 'DISABLED'}")
            logger.info(f"DeathLink: {'ENABLED' if dl_enabled else 'DISABLED'} (Amnesty: {dl_amnesty})")
            logger.info(f"Music Randomizer: {'ENABLED' if rand_music else 'DISABLED'}")
            logger.info(f"SFX Randomizer: {'ENABLED' if rand_sfx else 'DISABLED'}")
            logger.info("=" * 60)

        elif cmd == "ReceivedItems":
            for item in args.get("items", []):
                item_id = extract_item_id(item)
                self.item_mgr.process_new_item(item_id)

            # Sync unlocked tapes and keys to KatanaSave.zero
            self.save_mgr.sync_unlocks(
                unlocked_tapes=self.item_mgr.collected_tapes,
                unlocked_keys=self.item_mgr.keys,
                unlocked_swords=self.item_mgr.swords,
            )

    async def game_sync_loop(self) -> None:
        """Periodic background loop checking memory, game state, and incoming items."""
        while not self.exit_event.is_set():
            try:
                # 1. Process any incoming items from Archipelago items_received list
                if hasattr(self, "items_received"):
                    while self.last_received_item_index < len(self.items_received):
                        net_item = self.items_received[self.last_received_item_index]
                        self.last_received_item_index += 1
                        item_id = extract_item_id(net_item)
                        if len(self.item_mgr.received_items) < self.last_received_item_index:
                            self.item_mgr.process_new_item(item_id)
                            self.save_mgr.sync_unlocks(
                                unlocked_tapes=self.item_mgr.collected_tapes,
                                unlocked_keys=self.item_mgr.keys,
                                unlocked_swords=self.item_mgr.swords,
                            )

                # 2. Update memory state and check triggers
                self.game_state.update()
            except Exception as e:
                logger.error(f"Error in game sync loop: {e}")
            await asyncio.sleep(0.1)


async def main(args: Any) -> None:
    """Async main routine running the CommonContext client."""
    ctx = KatanaZeroContext(args.connect, args.password)
    ctx.auth = getattr(args, "name", None)

    ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
    ctx.game_sync_task = asyncio.create_task(ctx.game_sync_loop(), name="GameSyncLoop")

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()
