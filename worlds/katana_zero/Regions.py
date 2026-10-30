"""Region definitions for Katana ZERO Archipelago world."""

from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

from .Locations import KatanaZeroLocation, location_table

if TYPE_CHECKING:
    from . import KatanaZeroWorld

# All region names used by this world.
REGION_NAMES = [
    "Menu",
    "Factory Hideout",
    "Murdower Hotel",
    "Club Neon",
    "Mutual-Nil Prison",
    "Studio 51",
    "Mansion Hideout",
    "Chinatown",
    "Dragon Tape",
    "Slaughterhouse",
    "Bunker",
    "Government Lab",
    "Psychiatrist's Office",
]


def create_regions(world: "KatanaZeroWorld") -> None:
    """Create all regions, populate them with locations, and connect them to the Menu."""
    multiworld = world.multiworld
    player = world.player

    # Build active locations dictionary based on options
    active_locations: dict[str, LocationData] = dict(location_table)
    if world.options.enemysanity.value:
        from .Locations import enemy_location_table
        active_locations.update(enemy_location_table)

    # Build a lookup of region name → list of (location_name, location_data)
    region_to_locations: dict[str, list[tuple[str, int | None]]] = {name: [] for name in REGION_NAMES}
    for loc_name, loc_data in active_locations.items():
        if loc_data.region in region_to_locations:
            region_to_locations[loc_data.region].append((loc_name, loc_data.code))

    # Create Region objects and attach their locations.
    regions: dict[str, Region] = {}
    for region_name in REGION_NAMES:
        region = Region(region_name, player, multiworld)
        for loc_name, loc_code in region_to_locations[region_name]:
            location = KatanaZeroLocation(player, loc_name, loc_code, region)
            region.locations.append(location)
        regions[region_name] = region

    # Connect Menu → every non-Menu region.
    menu = regions["Menu"]
    for region_name, region in regions.items():
        if region_name == "Menu":
            continue
        menu.connect(region, f"Menu -> {region_name}")

    # Register all regions with the multiworld.
    multiworld.regions += regions.values()
