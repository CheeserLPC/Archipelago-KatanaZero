"""Archipelago Launcher Component Registration for Katana ZERO."""

from worlds.LauncherComponents import Component, Type, components, launch, icon_paths


def run_client(*args: str) -> None:
    """Launch Katana ZERO Archipelago Client via CommonContext in a dedicated window."""
    from .client.Launch import launch_katana_zero_client

    launch(launch_katana_zero_client, name="Katana ZERO Client", args=args)


# Register icon
icon_paths["katana_zero"] = f"ap:{__name__}/data/katana_zero.png"

# Register Katana ZERO Client with the Archipelago Launcher
components.append(
    Component(
        "Katana ZERO Client",
        func=run_client,
        game_name="Katana ZERO",
        component_type=Type.CLIENT,
        supports_uri=True,
        icon="katana_zero",
    )
)
