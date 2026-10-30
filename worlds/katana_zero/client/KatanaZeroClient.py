"""Katana ZERO Archipelago Multiworld Client.

Connects Katana ZERO to an Archipelago Multiworld server over WebSockets.
Coordinates memory hooking, save synchronizing, item unlocks,
trap effects, and DeathLink triggers with amnesty support.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Set
import uuid

import websockets

from .death_link_handler import DeathLinkHandler
from .game_state import GameStateTracker
from .item_manager import ItemManager
from .memory_reader import KatanaMemory
from .room_mappings import CHECK_DEFINITIONS, LOCATION_BY_ID
from .save_manager import SaveManager
from .trap_manager import TrapManager

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("KatanaZeroClient")


def extract_item_id(item: Any) -> int:
    """Robustly extract integer item_id from NetworkItem, dict, list/tuple, or int."""
    if hasattr(item, "item"):
        return int(item.item)
    if isinstance(item, dict):
        return int(item.get("item", 0))
    if isinstance(item, (list, tuple)) and len(item) > 0:
        return int(item[0])
    return int(item)


class KatanaZeroClient:
    """Main client coordinating network, game state, traps, and DeathLink."""

    def __init__(
        self,
        server: str = "localhost",
        port: int = 38281,
        player_name: str = "Zero",
        password: str = "",
    ) -> None:
        self.server = server
        self.port = port
        self.player_name = player_name
        self.password = password
        self.client_uuid = str(uuid.uuid4())

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running: bool = False
        self.connected_to_ap: bool = False
        self.team: int = 0
        self.slot: int = 0

        # Subsystems
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
        self.items = ItemManager(trap_callback=self.traps.trigger_trap)
        self.death_link = DeathLinkHandler(
            player_name=self.player_name,
            send_bounce_callback=self._send_deathlink_bounce,
            kill_player_callback=self._execute_kill_player,
        )
        self.game_state = GameStateTracker(
            memory=self.mem,
            item_manager=self.items,
            death_link=self.death_link,
            trap_manager=self.traps,
            send_check_callback=self._send_location_checks,
        )

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

    # ── DeathLink Callbacks ───────────────────────────────────────────────────

    def _execute_kill_player(self) -> None:
        """Trigger in-game instant kill."""
        logger.warning("[DEATHLINK] Incurring DeathLink fatality in Katana ZERO!")
        self.game_state.kill_player_in_game()

    def _send_deathlink_bounce(self, bounce_data: dict) -> None:
        """Send DeathLink Bounce packet to Archipelago server."""
        if not self.websocket or not self.connected_to_ap:
            return
        packet = [
            {
                "cmd": "Bounce",
                "tags": ["DeathLink"],
                "data": bounce_data,
            }
        ]
        asyncio.create_task(self._send_json(packet))

    def _send_location_checks(self, location_ids: List[int]) -> None:
        """Send LocationChecks packet to Archipelago server."""
        if not self.websocket or not self.connected_to_ap:
            return
        packet = [
            {
                "cmd": "LocationChecks",
                "locations": location_ids,
            }
        ]
        asyncio.create_task(self._send_json(packet))
        logger.info(f"[CHECKS SENT] Sent {len(location_ids)} location check(s) to Archipelago")

    async def _send_json(self, data: Any) -> None:
        """Send JSON packet over WebSocket."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send packet: {e}")

    # ── Archipelago Network Protocol ──────────────────────────────────────────

    async def connect_to_server(self) -> None:
        """Main connection and message dispatch loop."""
        uri = f"ws://{self.server}:{self.port}"
        logger.info(f"Connecting to Archipelago server at {uri}...")

        while self.running:
            try:
                async with websockets.connect(uri) as ws:
                    self.websocket = ws
                    logger.info("Connected to WebSocket! Awaiting RoomInfo...")

                    async for raw_msg in ws:
                        packets = json.loads(raw_msg)
                        for pkt in packets:
                            await self._handle_packet(pkt)

            except (websockets.ConnectionClosed, OSError) as e:
                self.connected_to_ap = False
                logger.warning(f"Connection lost ({e}). Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

    async def _handle_packet(self, packet: Dict[str, Any]) -> None:
        """Handle incoming Archipelago commands."""
        cmd = packet.get("cmd", "")

        if cmd == "RoomInfo":
            logger.info("Received RoomInfo. Sending Connect handshake...")
            connect_pkt = [
                {
                    "cmd": "Connect",
                    "password": self.password,
                    "game": "Katana ZERO",
                    "name": self.player_name,
                    "version": {"major": 0, "minor": 6, "build": 8, "class": "Version"},
                    "items_handling": 7,  # All items
                    "tags": ["DeathLink"],
                    "uuid": self.client_uuid,
                }
            ]
            await self._send_json(connect_pkt)

        elif cmd == "Connected":
            self.connected_to_ap = True
            self.team = packet.get("team", 0)
            self.slot = packet.get("slot", 1)

            slot_data = packet.get("slot_data", {})
            checked = set(packet.get("checked_locations", []))
            missing = set(packet.get("missing_locations", []))

            # Configure DeathLink and Amnesty from slot_data
            dl_enabled = bool(slot_data.get("death_link", 0))
            dl_amnesty = int(slot_data.get("death_link_amnesty", 0))
            self.death_link.set_config(enabled=dl_enabled, amnesty=dl_amnesty)

            self.game_state.set_location_info(checked, missing)
            if bool(slot_data.get("enemysanity", 0)):
                self.game_state.enemysanity_enabled = True

            # If abilities are not shuffled, unlock them immediately at start
            if not bool(slot_data.get("shuffle_chronos", 1)):
                self.items.mechanics["Chronos"] = True
            if not bool(slot_data.get("shuffle_throw", 1)):
                self.items.mechanics["Strength Training"] = True

            rand_music = bool(slot_data.get("randomize_music", 0))
            rand_sfx = bool(slot_data.get("randomize_sfx", 0))
            audio_seed = slot_data.get("audio_seed", None)
            if audio_seed is None:
                audio_seed = self.slot or 42

            self.mem.apply_audio_randomizer(
                randomize_music=rand_music,
                randomize_sfx=rand_sfx,
                seed=audio_seed,
            )

            logger.info("=" * 60)
            logger.info(f"[CONNECTED] CONNECTED TO MULTIWORLD AS '{self.player_name}' (Slot {self.slot})")
            logger.info(f"Goal: {slot_data.get('goal', 'Unknown')}")
            logger.info(f"Starting Tape: {slot_data.get('starting_tape', 'Factory')}")
            logger.info(f"Shuffle Chronos: {'ENABLED' if bool(slot_data.get('shuffle_chronos', 1)) else 'DISABLED'}")
            logger.info(f"Shuffle Strength Training: {'ENABLED' if bool(slot_data.get('shuffle_throw', 1)) else 'DISABLED'}")
            logger.info(f"Enemysanity: {'ENABLED' if self.game_state.enemysanity_enabled else 'DISABLED'}")
            logger.info(f"DeathLink: {'ENABLED' if dl_enabled else 'DISABLED'} (Amnesty: {dl_amnesty})")
            logger.info(f"Music Randomizer: {'ENABLED' if rand_music else 'DISABLED'}")
            logger.info(f"SFX Randomizer: {'ENABLED' if rand_sfx else 'DISABLED'}")
            logger.info("=" * 60)

        elif cmd == "ReceivedItems":
            items = packet.get("items", [])
            for item in items:
                item_id = extract_item_id(item)
                self.items.process_new_item(item_id)

            # Sync unlocked tapes and keys to KatanaSave.zero
            self.save_mgr.sync_unlocks(
                unlocked_tapes=self.items.collected_tapes,
                unlocked_keys=self.items.keys,
                unlocked_swords=self.items.swords,
            )

        elif cmd == "Bounced":
            tags = packet.get("tags", [])
            data = packet.get("data", {})
            if "DeathLink" in tags:
                self.death_link.on_incoming_deathlink(data)

        elif cmd == "ConnectionRefused":
            errors = packet.get("errors", [])
            logger.error(f"[CONNECTION REFUSED] By server: {errors}")
            self.running = False

        elif cmd == "PrintJSON":
            # Chat or system message from multiworld
            pass

    async def game_loop(self) -> None:
        """Periodic background task that ticks game state and checks memory."""
        while self.running:
            try:
                self.game_state.update()
            except Exception as e:
                logger.error(f"Error in game loop update: {e}")
            await asyncio.sleep(0.1)

    async def console_input_loop(self) -> None:
        """Read user commands from console."""
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                cmd = line.strip()
                if not cmd:
                    continue

                if cmd == "/help":
                    print("Available commands:")
                    print("  /status      - Show connection and memory status")
                    print("  /items       - List currently unlocked items and tapes")
                    print("  /checks      - List progress of checked locations")
                    print("  /deathlink   - Show DeathLink status and death counters")
                    print("  /sync        - Force write unlocked items to KatanaSave.zero")
                    print("  /die         - Simulate local player death (for testing)")
                    print("  /music       - Toggle Music Randomizer (or /music on|off)")
                    print("  /sfx         - Toggle Sound Effect Randomizer (or /sfx on|off)")
                    print("  /audio       - Show Audio Randomizer status")
                    print("  /quit        - Disconnect and exit")

                elif cmd == "/status":
                    print(f"Server: {self.server}:{self.port}")
                    print(f"Connected: {self.connected_to_ap}")
                    print(f"Memory Attached: {self.mem.is_attached()} (PID: {self.mem.pid})")
                    print(f"Current Room: {self.game_state.current_room or 'None'}")

                elif cmd == "/items":
                    print(f"Tapes ({len(self.items.collected_tapes)}/11): {sorted(self.items.collected_tapes)}")
                    print(f"Keys ({len(self.items.keys)}/5): {sorted(self.items.keys)}")
                    print(f"Swords: {sorted(self.items.swords)}")
                    print(f"Mechanics: {self.items.mechanics}")

                elif cmd == "/checks":
                    print(f"Completed: {len(self.game_state.checked_locations)}/40 checks")

                elif cmd == "/deathlink":
                    print(f"DeathLink Enabled: {self.death_link.enabled}")
                    print(f"Amnesty Limit: {self.death_link.amnesty_limit}")
                    print(f"Current Accumulated Deaths: {self.death_link.current_deaths}")
                    print(f"Lifetime Deaths: {self.death_link.total_deaths}")

                elif cmd == "/sync":
                    self.save_mgr.sync_unlocks(
                        unlocked_tapes=self.items.collected_tapes,
                        unlocked_keys=self.items.keys,
                        unlocked_swords=self.items.swords,
                    )
                    print("Saved data synchronized.")

                elif cmd == "/die":
                    print("Simulating local death...")
                    self.game_state.on_player_died()

                elif cmd.startswith("/music"):
                    parts = cmd.split(maxsplit=1)
                    arg = parts[1].lower() if len(parts) > 1 else ""
                    if arg in ("on", "1", "true"):
                        new_val = True
                    elif arg in ("off", "0", "false"):
                        new_val = False
                    else:
                        new_val = not self.mem.music_randomized
                    self.mem.apply_audio_randomizer(
                        randomize_music=new_val,
                        randomize_sfx=self.mem.sfx_randomized,
                        seed=self.mem.audio_seed or 42,
                    )
                    print(f"Music Randomizer is now {'ENABLED' if new_val else 'DISABLED'}.")

                elif cmd.startswith("/sfx"):
                    parts = cmd.split(maxsplit=1)
                    arg = parts[1].lower() if len(parts) > 1 else ""
                    if arg in ("on", "1", "true"):
                        new_val = True
                    elif arg in ("off", "0", "false"):
                        new_val = False
                    else:
                        new_val = not self.mem.sfx_randomized
                    self.mem.apply_audio_randomizer(
                        randomize_music=self.mem.music_randomized,
                        randomize_sfx=new_val,
                        seed=self.mem.audio_seed or 42,
                    )
                    print(f"SFX Randomizer is now {'ENABLED' if new_val else 'DISABLED'}.")

                elif cmd == "/audio":
                    print(
                        f"Audio Randomizer Status: Music={'SHUFFLED' if self.mem.music_randomized else 'VANILLA'}, "
                        f"SFX={'SHUFFLED' if self.mem.sfx_randomized else 'VANILLA'} (Hook Installed: {self.mem.audio_hook_installed})"
                    )

                elif cmd in ("/quit", "/exit"):
                    self.running = False
                    break

            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    async def run(self) -> None:
        """Run all concurrent client tasks."""
        self.running = True
        logger.info("Starting Katana ZERO Archipelago Client...")
        await asyncio.gather(
            self.connect_to_server(),
            self.game_loop(),
            self.console_input_loop(),
        )


def main(*args: str) -> None:
    """Entry point when executed from CLI or Archipelago Launcher."""
    import sys
    raw_args = list(args) if args else sys.argv[1:]

    # Parse args
    server = "localhost"
    port = 38281
    player = "Zero"
    password = ""

    # Check for CommonClient URL format or flags
    parser = argparse.ArgumentParser(description="Katana ZERO Archipelago Client")
    parser.add_argument("url", nargs="?", default="", help="Archipelago connection URL or host:port")
    parser.add_argument("--server", default="", help="Server hostname")
    parser.add_argument("--port", type=int, default=0, help="Server port")
    parser.add_argument("--player", "--name", default="", help="Player slot name")
    parser.add_argument("--password", default="", help="Server password")

    parsed, _ = parser.parse_known_args(raw_args)

    if parsed.url:
        u = parsed.url
        if u.startswith("archipelago://"):
            u = u[len("archipelago://"):]
        # Format: [user[:password]@]host[:port]
        if "@" in u:
            auth, hostport = u.split("@", 1)
            if ":" in auth:
                player, password = auth.split(":", 1)
            else:
                player = auth
        else:
            hostport = u
        if ":" in hostport:
            hp = hostport.split(":", 1)
            server = hp[0]
            try:
                port = int(hp[1].split("/")[0])
            except ValueError:
                port = 38281
        else:
            server = hostport.split("/")[0]

    if parsed.server:
        server = parsed.server
    if parsed.port:
        port = parsed.port
    if parsed.player:
        player = parsed.player
    if parsed.password:
        password = parsed.password

    client = KatanaZeroClient(
        server=server,
        port=port,
        player_name=player,
        password=password,
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("Client terminated by user.")


if __name__ == "__main__":
    main()
