"""Save file synchronizer for Katana ZERO.

Directly updates unlocked tapes, keys, and swords in KatanaSave.zero
in %LOCALAPPDATA%\\Katana_ZERO so the Apartment TV menu and Government Lab
reflect Archipelago item unlocks.
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import List, Optional, Set

logger = logging.getLogger("KatanaZeroClient.SaveManager")


def get_save_dir() -> str:
    """Return local appdata directory for Katana ZERO."""
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    return os.path.join(local_appdata, "Katana_ZERO")


class SaveManager:
    """Manages reading and synchronizing KatanaSave.zero."""

    def __init__(self, save_dir: Optional[str] = None) -> None:
        self.save_dir = save_dir or get_save_dir()
        self.save_file = os.path.join(self.save_dir, "KatanaSave.zero")
        self.backup_file = os.path.join(self.save_dir, "KatanaSave.zero.ap_backup")

    def ensure_backup(self) -> bool:
        """Create a backup of the original save file if none exists."""
        if os.path.exists(self.save_file) and not os.path.exists(self.backup_file):
            try:
                shutil.copyfile(self.save_file, self.backup_file)
                logger.info(f"Created initial save backup: {self.backup_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
                return False
        return True

    def read_lines(self) -> Optional[List[str]]:
        """Read all lines from KatanaSave.zero."""
        if not os.path.exists(self.save_file):
            return None
        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                return [line.rstrip("\r\n") for line in f]
        except Exception as e:
            logger.error(f"Error reading {self.save_file}: {e}")
            return None

    def sync_unlocks(
        self,
        unlocked_tapes: Set[str],
        unlocked_keys: Set[str],
        unlocked_swords: Set[str],
    ) -> bool:
        """Sync unlocked tapes, keys, and swords to save data."""
        lines = self.read_lines()
        if not lines:
            logger.warning(f"Save file not found at {self.save_file}")
            return False

        self.ensure_backup()

        modified = False

        # In KatanaSave.zero:
        # Lines 103-107 map to the 5 Government Lab keys (Prism, Master, Prototype, Phoenix, Savant)
        key_names = ["Prism Key", "Master Key", "Prototype Key", "Phoenix Key", "Savant Key"]
        for idx, key in enumerate(key_names):
            line_idx = 102 + idx  # 0-indexed (lines 103 to 107)
            if line_idx < len(lines):
                target_val = "1" if key in unlocked_keys else "0"
                if lines[line_idx] != target_val:
                    lines[line_idx] = target_val
                    modified = True

        if modified:
            try:
                # Write to temp file then atomic replace
                temp_file = self.save_file + ".tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    for line in lines:
                        f.write(line + "\n")
                shutil.move(temp_file, self.save_file)
                logger.info("Synchronized Archipelago unlocks to KatanaSave.zero")
                return True
            except Exception as e:
                logger.error(f"Failed to write updated save: {e}")
                return False

        return True
