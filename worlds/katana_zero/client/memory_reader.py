"""Win32 Memory Interface for Katana ZERO.

Uses standard Windows API via ctypes for low-overhead memory reading, writing,
and hook management directly in the running Katana ZERO.exe process without third-party dependencies.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import random
import struct
from typing import Dict, List, Optional

logger = logging.getLogger("KatanaZeroClient.Memory")

# Win32 Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260),
    ]


kernel32 = ctypes.windll.kernel32
CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
Process32First = kernel32.Process32First
Process32Next = kernel32.Process32Next
Module32First = kernel32.Module32First
Module32Next = kernel32.Module32Next
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle
ReadProcessMemory = kernel32.ReadProcessMemory
WriteProcessMemory = kernel32.WriteProcessMemory

VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
VirtualAllocEx.restype = wintypes.LPVOID

VirtualProtectEx = kernel32.VirtualProtectEx
VirtualProtectEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
VirtualProtectEx.restype = wintypes.BOOL

CreateRemoteThread = kernel32.CreateRemoteThread
CreateRemoteThread.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
CreateRemoteThread.restype = wintypes.HANDLE

# Offset definitions relative to image base
ROOM_ID_OFFSET = 0x20F8900
KILL_PLAYER_OFFSET = 0x488E90
ROOM_RESTART_OFFSET = 0x018E3450
ENEMY_HURT_OFFSET = 0x5BE9B0

# Trap offsets relative to image base
CONTROLS_INVERT_FAST_L = 0x47C492
CONTROLS_INVERT_SLOW_L = 0x47C49D
CONTROLS_INVERT_FAST_R = 0x47C545
CONTROLS_INVERT_SLOW_R = 0x47C550

FREEZE_PLAYER_OFFSET = 0x47C230
SLOWMO_CHECK_OFFSET = 0x438B30
ROLL_DISRUPTOR_OFFSET = 0x463800
PACIFIST_OFFSETS: List[int] = [0x453F00, 0x45B250, 0x44D0C0]
SCREEN_FLIP_HOOK_OFFSET = 0x0190EE70
INSTANCE_MANAGER_OFFSET = 0x20F88D8
PLAY_SOUND_INTERNAL_OFFSET = 0x019C6950

# Engine stability patch offsets relative to image base
YYGETREAL_ERROR_OFFSET = 0x18DDAB0
PLAYER_HURT_LINE330_OFFSET = 0x486B12

# Audio constants
TOTAL_SOUNDS = 884
MUSIC_IDS = list(range(1, 48))      # 1 to 47 inclusive (song_*.ogg)
GROUP0_SFX_IDS = (
    48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67,
    68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87,
    88, 89, 90, 91, 92, 93, 94, 95, 96, 98, 99, 100, 101, 102, 103, 104, 105, 107, 108, 109,
    110, 111, 112, 113, 115, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131,
    132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151,
    152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171,
    172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 188, 189, 190, 191, 192, 193, 194,
    195, 196, 197, 198, 199, 200, 201, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
    216, 217, 218, 219, 220, 221, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237,
    238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 257, 258, 259, 260,
    261, 262, 263, 264, 267, 269, 270, 272, 274, 275, 276, 277, 278, 279, 285, 286, 287, 288, 289, 290,
    291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310,
    311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 327, 328, 329, 330, 331,
    332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351,
    352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 364, 365, 366, 367, 368, 369, 387, 395, 396,
    397, 398, 399, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418,
    419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 442, 443, 444, 446, 447,
    449, 450, 451, 452, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 469, 470, 471, 472, 473, 474,
    475, 476, 477, 478, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495,
    496, 497, 498, 499, 500, 501, 502, 503, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525,
    526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 541, 542, 543, 544, 545, 546, 547,
    548, 549, 550, 551, 552, 553, 806, 807, 808, 809, 810, 811, 864, 874, 875, 876, 877, 878, 879, 880,
    881, 882,
)

# Mechanic function offsets in Katana ZERO.exe
MECHANIC_FUNCTIONS: Dict[str, List[int]] = {
    "Chronos": [0x438B30],              # player_bullettime_check
    "Dodge Roll": [],                   # Kept vanilla; disabled only via Roll Disruptor trap
    "Item Throw": [0x44D0C0],           # player_item_throw
    "Deflect": [],                      # Kept vanilla to preserve obj_record replay buffer
    "Wall Jump": [],                    # Kept vanilla per user request
}


class KatanaMemory:
    """Manages memory read/write operations and hooks for Katana ZERO.exe."""

    def __init__(self, target_process: str = "Katana ZERO.exe") -> None:
        self.target_name = target_process
        self.pid: Optional[int] = None
        self.handle: Optional[wintypes.HANDLE] = None
        self.base_address: int = 0
        self.module_size: int = 0

        # Hook state
        self.code_cave: Optional[int] = None
        self.death_counter_addr: Optional[int] = None
        self.death_hook_installed: bool = False
        self.screen_flip_cave: Optional[int] = None
        self.enemy_hook_cave: Optional[int] = None
        self.enemy_hook_installed: bool = False
        self.last_enemy_head: int = 0

        # Audio randomizer hook state
        self.audio_hook_cave: Optional[int] = None
        self.audio_table_addr: Optional[int] = None
        self.audio_hook_installed: bool = False
        self.music_randomized: bool = False
        self.sfx_randomized: bool = False
        self.audio_seed: Optional[int] = None

    def is_attached(self) -> bool:
        """Check if currently attached to a live process."""
        if not self.handle:
            return False
        exit_code = wintypes.DWORD()
        if kernel32.GetExitCodeProcess(self.handle, ctypes.byref(exit_code)):
            if exit_code.value == 259:  # STILL_ACTIVE
                return True
        self.detach()
        return False

    def attach(self) -> bool:
        """Search for target process and open handle."""
        self.detach()
        snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1:
            return False

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

        found_pid = None
        if Process32First(snapshot, ctypes.byref(entry)):
            while True:
                name = entry.szExeFile.decode("utf-8", "ignore")
                if name.lower() == self.target_name.lower():
                    found_pid = entry.th32ProcessID
                    break
                if not Process32Next(snapshot, ctypes.byref(entry)):
                    break

        CloseHandle(snapshot)

        if not found_pid:
            return False

        handle = OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
            False,
            found_pid,
        )
        if not handle:
            return False

        self.pid = found_pid
        self.handle = handle

        # Get module base
        mod_snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
        if mod_snap != -1:
            mod_entry = MODULEENTRY32()
            mod_entry.dwSize = ctypes.sizeof(MODULEENTRY32)
            if Module32First(mod_snap, ctypes.byref(mod_entry)):
                self.base_address = ctypes.cast(mod_entry.modBaseAddr, ctypes.c_void_p).value or 0
                self.module_size = mod_entry.modBaseSize
            CloseHandle(mod_snap)

        logger.info(
            f"Attached to {self.target_name} (PID: {self.pid}, Base: 0x{self.base_address:08X})"
        )

        # Install hooks & stability patches
        self.install_stability_patches()
        self.install_death_hook()
        self.install_enemy_kill_hook()
        if self.music_randomized or self.sfx_randomized:
            self.apply_audio_randomizer(self.music_randomized, self.sfx_randomized, self.audio_seed)
        return True

    def detach(self) -> None:
        """Close open process handle and reset state."""
        if self.handle:
            CloseHandle(self.handle)
            self.handle = None
        self.pid = None
        self.base_address = 0
        self.module_size = 0
        self.code_cave = None
        self.death_counter_addr = None
        self.death_hook_installed = False
        self.screen_flip_cave = None
        self.enemy_hook_cave = None
        self.enemy_hook_installed = False
        self.last_enemy_head = 0
        self.audio_hook_cave = None
        self.audio_table_addr = None
        self.audio_hook_installed = False

    def read_bytes(self, address: int, size: int) -> Optional[bytes]:
        """Read a raw buffer of bytes from process memory."""
        if not self.handle:
            return None
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        if ReadProcessMemory(self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(bytes_read)):
            return buf.raw[:bytes_read.value]
        return None

    def read_int32(self, address: int) -> Optional[int]:
        """Read a 32-bit signed integer."""
        raw = self.read_bytes(address, 4)
        if raw and len(raw) == 4:
            return int.from_bytes(raw, byteorder="little", signed=True)
        return None

    def read_uint32(self, address: int) -> Optional[int]:
        """Read a 32-bit unsigned integer."""
        raw = self.read_bytes(address, 4)
        if raw and len(raw) == 4:
            return int.from_bytes(raw, byteorder="little", signed=False)
        return None

    def write_bytes(self, address: int, data: bytes) -> bool:
        """Write raw bytes into process memory."""
        if not self.handle:
            return False
        buf = ctypes.create_string_buffer(data)
        bytes_written = ctypes.c_size_t(0)
        return bool(
            WriteProcessMemory(
                self.handle,
                ctypes.c_void_p(address),
                buf,
                len(data),
                ctypes.byref(bytes_written),
            )
        )

    def write_int32(self, address: int, value: int) -> bool:
        """Write a 32-bit signed integer."""
        return self.write_bytes(address, value.to_bytes(4, byteorder="little", signed=True))

    def read_current_room_id(self) -> Optional[int]:
        """Read active GameMaker room ID from memory."""
        if not self.is_attached() or not self.base_address:
            return None
        room_addr = self.base_address - 0x400000 + ROOM_ID_OFFSET
        return self.read_int32(room_addr)

    def install_stability_patches(self) -> bool:
        """Install engine stability patches to prevent GameMaker YYC fatal crashes:
        1. YYGetReal error block (0x18DDAB0):
           Safely defaults to 0.0 instead of calling YYError with 'REAL argument incorrect type'.
        2. player_hurt line 330 (0x486B12):
           Neutralizes empty with loop on dangling corpse/emitter pointer (fixes Bunker Headhunter crash).
        """
        if not self.is_attached():
            return False

        success = True
        try:
            old_protect = wintypes.DWORD()

            # 1. YYGetReal stability patch
            yy_va = self.base_address - 0x400000 + YYGETREAL_ERROR_OFFSET
            orig_yy = self.read_bytes(yy_va, 6)
            if orig_yy and orig_yy[0] != 0xEB:  # Not already patched with jmp short
                # jmp short +0x2a to 0x18DDADC (fld 0.0; pop esi; add esp, 8; ret)
                patch_yy = bytes.fromhex("eb2a90909090")
                VirtualProtectEx(self.handle, ctypes.c_void_p(yy_va), 6, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                if self.write_bytes(yy_va, patch_yy):
                    logger.info("Engine stability patch installed: YYGetReal safe fallback active.")
                else:
                    success = False
                VirtualProtectEx(self.handle, ctypes.c_void_p(yy_va), 6, old_protect.value, ctypes.byref(old_protect))

            # 2. player_hurt line 330 stability patch
            ph_va = self.base_address - 0x400000 + PLAYER_HURT_LINE330_OFFSET
            orig_ph = self.read_bytes(ph_va, 43)
            if orig_ph and orig_ph[0] != 0x31:  # Not already patched with xor eax, eax
                # xor eax, eax (2 bytes); jmp short +0x27 to 0x486B3D (2 bytes); nop * 39
                patch_ph = bytes([0x31, 0xC0, 0xEB, 0x27]) + b"\x90" * 39
                VirtualProtectEx(self.handle, ctypes.c_void_p(ph_va), 43, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                if self.write_bytes(ph_va, patch_ph):
                    logger.info("Script stability patch installed: player_hurt line 330 safeguarded.")
                else:
                    success = False
                VirtualProtectEx(self.handle, ctypes.c_void_p(ph_va), 43, old_protect.value, ctypes.byref(old_protect))

        except Exception as e:
            logger.error(f"Error installing stability patches: {e}")
            return False

        return success

    def install_death_hook(self) -> bool:
        """Install non-intrusive in-game atomic death counter hook on kill_player."""
        if not self.is_attached() or self.death_hook_installed:
            return self.death_hook_installed

        try:
            kill_player_va = self.base_address - 0x400000 + KILL_PLAYER_OFFSET
            orig_bytes = self.read_bytes(kill_player_va, 5)
            if not orig_bytes:
                return False

            # If already hooked (starts with E9), reuse or skip
            if orig_bytes[0] == 0xE9:
                logger.info("kill_player hook already present in running game.")
                self.death_hook_installed = True
                return True

            # Allocate 512 bytes for code cave
            cave = VirtualAllocEx(self.handle, None, 512, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
            if not cave:
                logger.error("VirtualAllocEx failed for death hook cave.")
                return False

            self.code_cave = cave
            self.death_counter_addr = cave
            self.write_int32(self.death_counter_addr, 0)

            # Trampoline code at cave + 0x20:
            # lock inc dword ptr [counter] -> F0 FF 05 <addr> (6 bytes)
            # Original instructions: 55 89 E5 53 57 (5 bytes)
            # jmp (kill_player_va + 5) -> E9 <rel32> (5 bytes)
            tramp_addr = cave + 0x20
            rel_return = (kill_player_va + 5) - (tramp_addr + 6 + 5 + 5)
            tramp_bytes = (
                b"\xF0\xFF\x05" + struct.pack("<I", self.death_counter_addr) +
                b"\x55\x89\xE5\x53\x57" +
                b"\xE9" + struct.pack("<i", rel_return)
            )
            self.write_bytes(tramp_addr, tramp_bytes)

            # Patch kill_player_va: jmp tramp_addr (E9 <rel32>)
            old_protect = wintypes.DWORD()
            VirtualProtectEx(self.handle, ctypes.c_void_p(kill_player_va), 5, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
            rel_cave = tramp_addr - (kill_player_va + 5)
            self.write_bytes(kill_player_va, b"\xE9" + struct.pack("<i", rel_cave))
            VirtualProtectEx(self.handle, ctypes.c_void_p(kill_player_va), 5, old_protect.value, ctypes.byref(old_protect))

            self.death_hook_installed = True
            logger.info(f"Death hook installed at 0x{kill_player_va:08X} (counter at 0x{self.death_counter_addr:08X})")
            return True
        except Exception as e:
            logger.error(f"Error installing death hook: {e}")
            return False

    def read_death_count(self) -> int:
        """Read atomic death count from hook cave."""
        if not self.death_counter_addr:
            return 0
        return self.read_int32(self.death_counter_addr) or 0

    def install_enemy_kill_hook(self) -> bool:
        """Install non-intrusive hook on gml_Script_enemy_hurt to capture enemy kill instance IDs."""
        if not self.is_attached() or self.enemy_hook_installed:
            return self.enemy_hook_installed

        try:
            enemy_hurt_va = self.base_address - 0x400000 + ENEMY_HURT_OFFSET
            orig_bytes = self.read_bytes(enemy_hurt_va, 5)
            if not orig_bytes:
                return False

            # If already hooked (starts with E9), locate existing cave
            if orig_bytes[0] == 0xE9:
                rel_offset = int.from_bytes(orig_bytes[1:5], byteorder="little", signed=True)
                tramp_addr = enemy_hurt_va + 5 + rel_offset
                self.enemy_hook_cave = tramp_addr - 0x110
                self.enemy_hook_installed = True
                self.last_enemy_head = self.read_uint32(self.enemy_hook_cave) or 0
                logger.info(
                    f"Existing enemy_hurt hook detected (cave: 0x{self.enemy_hook_cave:08X}, head: {self.last_enemy_head})"
                )
                return True

            # Allocate 512 bytes for code cave
            cave = VirtualAllocEx(self.handle, None, 512, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
            if not cave:
                logger.error("VirtualAllocEx failed for enemy hook cave.")
                return False

            self.enemy_hook_cave = cave
            # Zero out head counter, reserved fields, and ring buffer
            self.write_bytes(cave, b"\x00" * 256)
            self.last_enemy_head = 0

            ring_buf = cave + 8
            ret_addr = enemy_hurt_va + 5
            tramp_addr = cave + 0x110

            code = (
                b"\x52"
                + b"\x50"
                + b"\x8B\x44\x24\x0C"
                + b"\x85\xC0"
                + b"\x74\x1C"
                + b"\x8B\x50\x78"
                + b"\x85\xD2"
                + b"\x74\x15"
                + b"\xA1" + struct.pack("<I", cave)
                + b"\x83\xE0\x3F"
                + b"\x89\x14\x85" + struct.pack("<I", ring_buf)
                + b"\xFF\x05" + struct.pack("<I", cave)
                + b"\x58"
                + b"\x5A"
                + b"\x55"
                + b"\x89\xE5"
                + b"\x53"
                + b"\x57"
            )
            rel_ret = ret_addr - (tramp_addr + len(code) + 5)
            code += b"\xE9" + struct.pack("<i", rel_ret)
            self.write_bytes(tramp_addr, code)

            # Patch enemy_hurt_va: jmp tramp_addr (E9 <rel32>)
            old_protect = wintypes.DWORD()
            VirtualProtectEx(self.handle, ctypes.c_void_p(enemy_hurt_va), 5, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
            rel_cave = tramp_addr - (enemy_hurt_va + 5)
            self.write_bytes(enemy_hurt_va, b"\xE9" + struct.pack("<i", rel_cave))
            VirtualProtectEx(self.handle, ctypes.c_void_p(enemy_hurt_va), 5, old_protect.value, ctypes.byref(old_protect))

            self.enemy_hook_installed = True
            logger.info(f"Enemy kill hook installed at 0x{enemy_hurt_va:08X} (cave: 0x{cave:08X})")
            return True
        except Exception as e:
            logger.error(f"Error installing enemy kill hook: {e}")
            return False

    def read_killed_enemy_ids(self) -> List[int]:
        """Read newly recorded enemy instance IDs from the hook ring buffer."""
        if not self.enemy_hook_cave:
            return []

        head = self.read_uint32(self.enemy_hook_cave)
        if head is None:
            return []

        if head < self.last_enemy_head:
            # Cave was reset or game restarted
            self.last_enemy_head = 0

        if head == self.last_enemy_head:
            return []

        new_ids: List[int] = []
        # In case head jumped by more than buffer size (64), cap to last 64
        start_idx = max(self.last_enemy_head, head - 64)
        for idx in range(start_idx, head):
            slot = idx & 0x3F
            iid = self.read_uint32(self.enemy_hook_cave + 8 + slot * 4)
            if iid and iid > 0:
                new_ids.append(iid)

        self.last_enemy_head = head
        return new_ids

    def install_audio_hook(self) -> bool:
        """Install non-intrusive hook on PlaySoundInternal to enable live sound/music remapping."""
        if not self.is_attached() or self.audio_hook_installed:
            return self.audio_hook_installed

        try:
            target_va = self.base_address - 0x400000 + PLAY_SOUND_INTERNAL_OFFSET
            orig_bytes = self.read_bytes(target_va, 6)
            if not orig_bytes:
                return False

            # If already hooked (starts with E9), locate existing cave
            if orig_bytes[0] == 0xE9:
                rel_offset = int.from_bytes(orig_bytes[1:5], byteorder="little", signed=True)
                cave = target_va + 5 + rel_offset
                self.audio_hook_cave = cave
                self.audio_table_addr = cave + 0x100
                logger.info(
                    f"Existing audio randomizer hook detected (cave: 0x{self.audio_hook_cave:08X}), updating trampoline..."
                )
            else:
                # Verify vanilla prologue: 55 8B EC 83 EC 1C
                if orig_bytes != b"\x55\x8B\xEC\x83\xEC\x1C":
                    logger.error(
                        f"Audio hook target 0x{target_va:08X} has unexpected bytes: {orig_bytes.hex(' ')}"
                    )
                    return False

                # Allocate 4096 bytes for code cave and remap table
                cave = VirtualAllocEx(self.handle, None, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
                if not cave:
                    logger.error("VirtualAllocEx failed for audio randomizer cave.")
                    return False

                self.audio_hook_cave = cave
                self.audio_table_addr = cave + 0x100

                # Initialize identity table [0, 1, ..., 883]
                identity = list(range(TOTAL_SOUNDS))
                raw_table = struct.pack(f"<{len(identity)}I", *identity)
                self.write_bytes(self.audio_table_addr, raw_table)

            # Build trampoline code
            # In PlaySoundInternal(sound_id, priority, loop):
            # [esp+4] = sound_id
            # When pushing eax and edx, ESP drops by 8:
            # [esp+0x0C] = sound_id
            # [esp+0x18] = loop boolean (0 = one-shot, !=0 = looping)
            code_parts = bytearray()
            code_parts += b"\x50"                                 # push eax
            code_parts += b"\x52"                                 # push edx
            code_parts += b"\x8B\x44\x24\x0C"                     # mov eax, [esp+0xC]
            code_parts += b"\x85\xC0"                             # test eax, eax
            js_idx = len(code_parts)
            code_parts += b"\x78\x00"                             # js finish
            code_parts += b"\x3D\x73\x03\x00\x00"                 # cmp eax, 883
            jge_idx = len(code_parts)
            code_parts += b"\x7D\x00"                             # jge finish

            # Check if this is SFX (sound_id >= 48) and requested to loop (loop != 0)
            code_parts += b"\x83\xF8\x30"                         # cmp eax, 48
            code_parts += b"\x7C\x07"                             # jl do_remap (skip loop check for music)
            code_parts += b"\x83\x7C\x24\x18\x00"                 # cmp dword ptr [esp+0x18], 0
            loop_idx = len(code_parts)
            code_parts += b"\x75\x00"                             # jne finish (skip remap if looping SFX)

            # do_remap:
            code_parts += b"\xBA" + struct.pack("<I", self.audio_table_addr) # mov edx, table_addr
            code_parts += b"\x8B\x04\x82"                         # mov eax, [edx+eax*4]
            code_parts += b"\x89\x44\x24\x0C"                     # mov [esp+0xC], eax

            finish_idx = len(code_parts)
            code_parts[js_idx + 1] = finish_idx - (js_idx + 2)
            code_parts[jge_idx + 1] = finish_idx - (jge_idx + 2)
            code_parts[loop_idx + 1] = finish_idx - (loop_idx + 2)

            code_parts += b"\x5A"                                 # pop edx
            code_parts += b"\x58"                                 # pop eax
            # Original displaced 6 bytes of PlaySoundInternal:
            # 55          push ebp
            # 8B EC       mov ebp, esp
            # 83 EC 1C    sub esp, 0x1C
            code_parts += b"\x55"
            code_parts += b"\x8B\xEC"
            code_parts += b"\x83\xEC\x1C"

            # JMP back to target_va + 6
            curr_pos = cave + len(code_parts)
            rel_back = (target_va + 6) - (curr_pos + 5)
            code_parts += b"\xE9" + struct.pack("<i", rel_back)

            self.write_bytes(cave, bytes(code_parts))

            # Install hook on target_va: JMP cave + NOP (6 bytes total)
            rel_hook = cave - (target_va + 5)
            hook_bytes = b"\xE9" + struct.pack("<i", rel_hook) + b"\x90"

            old_prot = wintypes.DWORD()
            VirtualProtectEx(self.handle, ctypes.c_void_p(target_va), 6, PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot))
            self.write_bytes(target_va, hook_bytes)
            VirtualProtectEx(self.handle, ctypes.c_void_p(target_va), 6, old_prot.value, ctypes.byref(old_prot))

            self.audio_hook_installed = True
            logger.info(
                f"Audio randomizer hook installed at PlaySoundInternal 0x{target_va:08X} "
                f"(cave: 0x{cave:08X}, table: 0x{self.audio_table_addr:08X})"
            )
            return True
        except Exception as e:
            logger.error(f"Error installing audio randomizer hook: {e}")
            return False

    def apply_audio_randomizer(
        self,
        randomize_music: bool = False,
        randomize_sfx: bool = False,
        seed: Optional[int] = None,
    ) -> bool:
        """Apply or update music and SFX shuffle in process memory."""
        self.music_randomized = randomize_music
        self.sfx_randomized = randomize_sfx
        if seed is not None:
            self.audio_seed = seed
        elif self.audio_seed is None:
            self.audio_seed = 42

        # If neither is requested, uninstall hook if installed to keep process vanilla
        if not randomize_music and not randomize_sfx:
            if self.audio_hook_installed:
                self.uninstall_audio_hook()
            return True

        if not self.audio_hook_installed:
            if not self.install_audio_hook():
                return False

        if not self.audio_table_addr:
            return False

        # Build remapping table (identity default for all 884 IDs)
        remap = list(range(TOTAL_SOUNDS))

        # 1. Music tracks (IDs 1..47)
        if randomize_music:
            rng_music = random.Random((self.audio_seed + 101) & 0xFFFFFFFF)
            shuffled_music = list(MUSIC_IDS)
            rng_music.shuffle(shuffled_music)
            for i, orig_id in enumerate(MUSIC_IDS):
                remap[orig_id] = shuffled_music[i]

        # 2. Sound effects (strictly Audio Group 0 IDs, permanently resident in memory)
        if randomize_sfx:
            sfx_pool = list(GROUP0_SFX_IDS)
            rng_sfx = random.Random((self.audio_seed + 202) & 0xFFFFFFFF)
            shuffled_sfx = list(sfx_pool)
            rng_sfx.shuffle(shuffled_sfx)
            for j, orig_id in enumerate(sfx_pool):
                remap[orig_id] = shuffled_sfx[j]

        raw_table = struct.pack(f"<{len(remap)}I", *remap)
        ok = self.write_bytes(self.audio_table_addr, raw_table)
        if ok:
            logger.info(
                f"Audio randomizer updated: Music={'SHUFFLED' if randomize_music else 'VANILLA'}, "
                f"SFX={'SHUFFLED' if randomize_sfx else 'VANILLA'} (Seed: {self.audio_seed})"
            )
        return ok

    def uninstall_audio_hook(self) -> bool:
        """Restore original bytes at PlaySoundInternal and reset identity."""
        if not self.is_attached() or not self.audio_hook_installed:
            return True

        target_va = self.base_address - 0x400000 + PLAY_SOUND_INTERNAL_OFFSET
        orig_bytes = b"\x55\x8B\xEC\x83\xEC\x1C"

        old_prot = wintypes.DWORD()
        VirtualProtectEx(self.handle, ctypes.c_void_p(target_va), 6, PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot))
        self.write_bytes(target_va, orig_bytes)
        VirtualProtectEx(self.handle, ctypes.c_void_p(target_va), 6, old_prot.value, ctypes.byref(old_prot))

        if self.audio_table_addr:
            identity = list(range(TOTAL_SOUNDS))
            self.write_bytes(self.audio_table_addr, struct.pack(f"<{len(identity)}I", *identity))

        self.audio_hook_installed = False
        self.music_randomized = False
        self.sfx_randomized = False
        logger.info("Audio randomizer hook uninstalled; vanilla audio restored.")
        return True

    def set_mechanic_state(self, mechanic_name: str, unlocked: bool) -> bool:
        """Lock or unlock a player mechanic by patching function entry with RET (0xC3) or push ebp (0x55)."""
        if not self.is_attached() or not self.base_address:
            return False

        offsets = MECHANIC_FUNCTIONS.get(mechanic_name, [])
        target_byte = b"\x55" if unlocked else b"\xC3"

        success = True
        old_protect = wintypes.DWORD()
        for off in offsets:
            va = self.base_address - 0x400000 + off
            cur = self.read_bytes(va, 1)
            if cur != target_byte:
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                ok = self.write_bytes(va, target_byte)
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, old_protect.value, ctypes.byref(old_protect))
                if not ok:
                    success = False
        return success

    def kill_player_remote(self) -> bool:
        """Execute in-game player elimination for incoming DeathLink signal."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            rr_fn = self.base_address - 0x400000 + ROOM_RESTART_OFFSET
            h_thread = CreateRemoteThread(self.handle, None, 0, ctypes.c_void_p(rr_fn), None, 0, None)
            if h_thread:
                CloseHandle(h_thread)
                logger.info("In-game death / room restart executed via remote thread.")
                return True
        except Exception as e:
            logger.error(f"Failed to kill player remotely: {e}")
        return False

    def set_controls_inverted(self, inverted: bool) -> bool:
        """Invert or restore player horizontal movement controls."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            old_protect = wintypes.DWORD()
            patches = [
                (CONTROLS_INVERT_FAST_L, b"\x70\x66" if inverted else b"\xE0\x65"),
                (CONTROLS_INVERT_SLOW_L, b"\x67\x06" if inverted else b"\x5E\x06"),
                (CONTROLS_INVERT_FAST_R, b"\xE0\x65" if inverted else b"\x70\x66"),
                (CONTROLS_INVERT_SLOW_R, b"\x5E\x06" if inverted else b"\x67\x06"),
            ]
            for offset, data in patches:
                va = self.base_address - 0x400000 + offset
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                self.write_bytes(va, data)
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), len(data), old_protect.value, ctypes.byref(old_protect))
            logger.info(f"Controls inversion set to: {inverted}")
            return True
        except Exception as e:
            logger.error(f"Failed to set controls inverted: {e}")
            return False

    def set_player_frozen(self, frozen: bool) -> bool:
        """Freeze or unfreeze player input and movement processing."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            va = self.base_address - 0x400000 + FREEZE_PLAYER_OFFSET
            old_protect = wintypes.DWORD()
            byte_val = b"\xC3" if frozen else b"\x55"
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
            self.write_bytes(va, byte_val)
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, old_protect.value, ctypes.byref(old_protect))
            logger.info(f"Player frozen set to: {frozen}")
            return True
        except Exception as e:
            logger.error(f"Failed to set player frozen: {e}")
            return False

    def set_slowmo_disabled(self, disabled: bool) -> bool:
        """Disable or restore Chronos slow-mo ability."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            va = self.base_address - 0x400000 + SLOWMO_CHECK_OFFSET
            old_protect = wintypes.DWORD()
            byte_val = b"\xC3" if disabled else b"\x55"
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
            self.write_bytes(va, byte_val)
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, old_protect.value, ctypes.byref(old_protect))
            logger.info(f"Slow-mo disabled set to: {disabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to set slow-mo disabled: {e}")
            return False

    def set_roll_disabled(self, disabled: bool) -> bool:
        """Disable or restore dodge roll ability."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            va = self.base_address - 0x400000 + ROLL_DISRUPTOR_OFFSET
            old_protect = wintypes.DWORD()
            byte_val = b"\xC3" if disabled else b"\x55"
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
            self.write_bytes(va, byte_val)
            VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, old_protect.value, ctypes.byref(old_protect))
            logger.info(f"Roll disabled set to: {disabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to set roll disabled: {e}")
            return False

    def set_attack_disabled(self, disabled: bool) -> bool:
        """Disable or restore player attack button (sword slash) and item throw."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            old_protect = wintypes.DWORD()
            byte_val = b"\xC3" if disabled else b"\x55"
            for off in PACIFIST_OFFSETS:
                va = self.base_address - 0x400000 + off
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                self.write_bytes(va, byte_val)
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 1, old_protect.value, ctypes.byref(old_protect))
            logger.info(f"Pacifist Trap (attack + throw disabled) set to: {disabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to set attack disabled: {e}")
            return False

    def set_screen_flipped(self, flipped: bool) -> bool:
        """Invert application surface presentation to flip screen upside down."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            va = self.base_address - 0x400000 + SCREEN_FLIP_HOOK_OFFSET
            old_protect = wintypes.DWORD()

            if flipped:
                if not self.screen_flip_cave:
                    cave = VirtualAllocEx(self.handle, None, 256, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
                    if not cave:
                        logger.error("VirtualAllocEx failed for screen flip cave.")
                        return False

                    # Sign bit mask at cave
                    self.write_bytes(cave, b"\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

                    tramp = cave + 16
                    ret_addr = va + 0x22
                    code = (
                        b"\x0F\x57\x15" + struct.pack("<I", cave) +
                        b"\xF3\x0F\x11\x54\x24\x14" +
                        b"\xF3\x0F\x5E\xC8" +
                        b"\xF3\x0F\x10\x44\x24\x30" +
                        b"\xF3\x0F\x58\x44\x24\x38" +
                        b"\xF3\x0F\x11\x4C\x24\x10" +
                        b"\xF3\x0F\x11\x44\x24\x0C" +
                        b"\xF3\x0F\x10\x44\x24\x2C"
                    )
                    rel_ret = ret_addr - (tramp + len(code) + 5)
                    code += b"\xE9" + struct.pack("<i", rel_ret)
                    self.write_bytes(tramp, code)
                    self.screen_flip_cave = cave

                rel_cave = (self.screen_flip_cave + 16) - (va + 5)
                patch = b"\xE9" + struct.pack("<i", rel_cave) + b"\x90"
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 6, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                self.write_bytes(va, patch)
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 6, old_protect.value, ctypes.byref(old_protect))
            else:
                # Restore original 6 bytes
                orig = b"\xF3\x0F\x11\x54\x24\x14"
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 6, PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect))
                self.write_bytes(va, orig)
                VirtualProtectEx(self.handle, ctypes.c_void_p(va), 6, old_protect.value, ctypes.byref(old_protect))

            logger.info(f"Screen flip set to: {flipped}")
            return True
        except Exception as e:
            logger.error(f"Failed to set screen flip: {e}")
            return False

    def get_player_instance(self) -> Optional[int]:
        """Find player CInstance pointer in active (0x80) or deactivated (0x8C) instance lists."""
        if not self.is_attached() or not self.base_address:
            return None

        mgr_va = self.base_address - 0x400000 + INSTANCE_MANAGER_OFFSET
        manager_ptr = self.read_uint32(mgr_va)
        if not manager_ptr:
            return None

        for offset in (0x80, 0x8C):
            curr = self.read_uint32(manager_ptr + offset)
            count = 0
            while curr and count < 300:
                meta_ptr = self.read_uint32(curr + 0x68)
                if meta_ptr:
                    name_ptr = self.read_uint32(meta_ptr)
                    if name_ptr:
                        raw_name = self.read_bytes(name_ptr, 32)
                        name = raw_name.split(b"\x00")[0].decode("ascii", "ignore") if raw_name else ""
                        if name == "obj_player":
                            return curr
                curr = self.read_uint32(curr + 0x130)
                count += 1
        return None

    def get_player_position(self) -> Optional[tuple[float, float]]:
        """Get the current (x, y) coordinates of the player."""
        inst = self.get_player_instance()
        if not inst:
            return None
        x_raw = self.read_bytes(inst + 0xA0, 4)
        y_raw = self.read_bytes(inst + 0xA4, 4)
        if x_raw and y_raw and len(x_raw) == 4 and len(y_raw) == 4:
            x = struct.unpack("<f", x_raw)[0]
            y = struct.unpack("<f", y_raw)[0]
            return (x, y)
        return None

    def teleport_player(self, rx: float = 0.0, ry: float = 0.0) -> bool:
        """Teleport player instance safely to room's designated level spawn or safe ground displacement."""
        if not self.is_attached() or not self.base_address:
            return False

        try:
            player_inst = self.get_player_instance()
            if not player_inst:
                logger.warning("Could not find obj_player to teleport.")
                return False

            # Read xstart (offset +0xAC) and ystart (offset +0xD0)
            xs_raw = self.read_bytes(player_inst + 0xAC, 4)
            ys_raw = self.read_bytes(player_inst + 0xD0, 4)
            tx, ty = None, None
            if xs_raw and ys_raw and len(xs_raw) == 4 and len(ys_raw) == 4:
                tx_cand = struct.unpack("<f", xs_raw)[0]
                ty_cand = struct.unpack("<f", ys_raw)[0]
                if 100.0 < tx_cand < 20000.0 and 100.0 < ty_cand < 20000.0:
                    tx, ty = tx_cand, ty_cand

            # Fallback to horizontal displacement on current ground elevation
            if tx is None or ty is None:
                cur_pos = self.get_player_position()
                if cur_pos:
                    import random
                    cur_x, cur_y = cur_pos
                    mgr_va = self.base_address - 0x400000 + INSTANCE_MANAGER_OFFSET
                    manager_ptr = self.read_uint32(mgr_va)
                    rw = self.read_uint32(manager_ptr + 0x10) or 1920
                    offset = random.choice([-250.0, 250.0])
                    tx = max(100.0, min(float(rw) - 100.0, cur_x + offset))
                    ty = cur_y
                else:
                    return False

            # Set dirty flag (0x74 |= 8) so engine syncs bounding box & spatial grid
            flags = self.read_uint32(player_inst + 0x74) or 0
            self.write_uint32(player_inst + 0x74, flags | 0x8)

            # Update coordinates (x, y, xprevious, yprevious)
            self.write_bytes(player_inst + 0xA0, struct.pack("<f", tx))
            self.write_bytes(player_inst + 0xB0, struct.pack("<f", tx))
            self.write_bytes(player_inst + 0xA4, struct.pack("<f", ty))
            self.write_bytes(player_inst + 0xB4, struct.pack("<f", ty))
            logger.info(f"Spatial Warp: Teleported player safely to ({tx:.1f}, {ty:.1f})")
            return True
        except Exception as e:
            logger.error(f"Failed to teleport player: {e}")
            return False
