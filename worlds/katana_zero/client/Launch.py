"""Launcher entry point for Katana ZERO client."""

import asyncio
from typing import Sequence

try:
    import colorama
    from CommonClient import get_base_parser, handle_url_arg

    HAS_COMMON_CLIENT = True
except ImportError:
    HAS_COMMON_CLIENT = False


def launch_katana_zero_client(*args: Sequence[str]) -> None:
    """Launch the client using Archipelago CommonContext or standalone fallback."""
    if HAS_COMMON_CLIENT:
        from .context import main

        parser = get_base_parser()
        parser.add_argument("--name", default=None, help="Slot Name to connect as.")
        parser.add_argument("url", nargs="?", help="Archipelago connection url")

        launch_args = handle_url_arg(parser.parse_args(args))

        colorama.just_fix_windows_console()
        asyncio.run(main(launch_args))
        colorama.deinit()
    else:
        from .KatanaZeroClient import main as standalone_main
        standalone_main(*args)
