# AI Usage & Development Disclaimer

This document outlines the scope and role of Artificial Intelligence assistance utilized during the development, reverse engineering, and debugging of the **Katana ZERO Archipelago Multiworld Integration**.

---

##  Tool Attribution
Development of this project was conducted through pair programming with **Google Antigravity**, an agentic AI coding assistant developed by **Google DeepMind**.

---

##  Scope of AI Assistance

Google Antigravity was utilized for technical assistance in the following areas:

### 1. Advanced Debugging & Reverse Engineering
- **GameMaker Studio YYC (Native x86) Disassembly:** Analyzing compiled assembly routines, function call conventions, virtual method dispatch tables, and GML script execution paths within `Katana ZERO.exe`.
- **Root Cause Analysis of Engine Crashes:** Diagnosing native GameMaker runtime assertion failures, including:
  - The fatal `REAL argument incorrect type` crash occurring during the Bunker boss fight against Headhunter (`obj_headhunter_energy_bullet_Draw_0` calling `gml_Script_player_hurt` at line 330).
  - The audio handle tracking desynchronization crash in `obj_sfxmaster_Step_2` (line 207).

### 2. Live In-Memory Inspection & Editing (Active Process Hooking)
- **Live Memory Analysis:** Reading, inspecting, and verifying game structures, room IDs, and instance registries directly in memory while `Katana ZERO.exe` was actively running.
- **Code Cave & Trampoline Construction:** Assisting in the calculation of relative offsets, machine opcode generation, and allocation of executable memory (`VirtualAllocEx` / `VirtualProtectEx`) for:
  - The non-intrusive atomic death counter hook on `kill_player` (`0x00488E90`).
  - The Enemysanity kill-detection ring buffer hook on `gml_Script_enemy_hurt` (`0x005BE9B0`).
  - The in-memory Audio Group 0 sound effect and music remapping table hook at `PlaySoundInternal` (`0x01A96950`).
- **Live Patch Verification:** Applying and validating live assembly patches on running game processes to verify that boss fight crashes and infinite audio loops were permanently eliminated before finalizing code.

### 3. Bug Fixing & Inline Patch Engineering
- **Safe Fallback Engineering:** Designing dual-layer stability protections, including the global `YYGetReal` fallback at `0x018DDAB0` and the `player_hurt` line 330 safeguard, allowing the engine to gracefully handle unexpected type tags without terminating the process.
- **Audio Loop Guards:** Implementing assembly checks to inspect the `loop` flag parameter in `PlaySoundInternal`, preventing one-shot sound effects from infinitely looping during VHS rewind and pause sequences.

### 4. Technical Rubber-Ducking & Architecture Design
- **Logic & Rules Structuring:** Validating multiworld item classifications, human written code, region connections, and accessibility logic across all win-condition goals.
- **Architecture Ideation:** Refining game mechanics, such as the 7 in-game combat traps (Chronos Overdose, Freeze Trap, Chronos Disruptor, Screen Flip, Spatial Warp, Roll Disruptor, and Pacifist Trap).
- **DeathLink & Amnesty Logic:** Designing debouncing windows and amnesty limits

---

##  Human First Programming, & Final Responsibility
All project objectives, gameplay designs, architecture decisions, and code integrations were designed, directed, supervised, tested, and verified by **CheeserLPC**. Every feature has been tested in live gameplay to ensure stability, balance, and adherence to Archipelago standards.
