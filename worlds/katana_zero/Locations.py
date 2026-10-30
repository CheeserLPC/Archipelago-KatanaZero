"""Location definitions for Katana ZERO Archipelago world."""

from typing import Dict, NamedTuple, Optional

from BaseClasses import Location


class KatanaZeroLocation(Location):
    """Represents a check location in the Katana ZERO game world."""
    game = "Katana ZERO"


class LocationData(NamedTuple):
    """Data class for location definitions.

    Attributes:
        code: The unique numeric ID for this location, or None for events.
        region: The region this location belongs to.
    """
    code: Optional[int]
    region: str


# Base location ID for Katana ZERO (range: 82200000 – 82200099)
BASE_LOCATION_ID = 82200000

location_table: Dict[str, LocationData] = {
    # ── Stage Clears ── IDs 82200000-82200010
    "Factory - Tape Completed":        LocationData(BASE_LOCATION_ID + 0,  "Factory Hideout"),
    "Hotel - Tape Completed":          LocationData(BASE_LOCATION_ID + 1,  "Murdower Hotel"),
    "Club - Tape Completed":           LocationData(BASE_LOCATION_ID + 2,  "Club Neon"),
    "Prison - Tape Completed":         LocationData(BASE_LOCATION_ID + 3,  "Mutual-Nil Prison"),
    "Studio 51 - Tape Completed":      LocationData(BASE_LOCATION_ID + 4,  "Studio 51"),
    "Mansion - Tape Completed":        LocationData(BASE_LOCATION_ID + 5,  "Mansion Hideout"),
    "Chinatown - Tape Completed":      LocationData(BASE_LOCATION_ID + 6,  "Chinatown"),
    "Dragon - Tape Completed":         LocationData(BASE_LOCATION_ID + 7,  "Dragon Tape"),
    "Slaughterhouse - Tape Completed": LocationData(BASE_LOCATION_ID + 8,  "Slaughterhouse"),
    "Bunker - Tape Completed":         LocationData(BASE_LOCATION_ID + 9,  "Bunker"),
    "Government Lab - Tape Completed": LocationData(BASE_LOCATION_ID + 10, "Government Lab"),

    # ── Mid-Stage Milestones ── IDs 82200011-82200030
    "Factory - Upper Floors Cleared":       LocationData(BASE_LOCATION_ID + 11, "Factory Hideout"),
    "Factory - Rooftop Reached":            LocationData(BASE_LOCATION_ID + 12, "Factory Hideout"),
    "Hotel - Lobby Cleared":                LocationData(BASE_LOCATION_ID + 13, "Murdower Hotel"),
    "Hotel - Penthouse Reached":            LocationData(BASE_LOCATION_ID + 14, "Murdower Hotel"),
    "Club - Dance Floor Cleared":           LocationData(BASE_LOCATION_ID + 15, "Club Neon"),
    "Club - VIP Lounge Reached":            LocationData(BASE_LOCATION_ID + 16, "Club Neon"),
    "Prison - Cell Block Cleared":          LocationData(BASE_LOCATION_ID + 17, "Mutual-Nil Prison"),
    "Prison - Warden Office Reached":       LocationData(BASE_LOCATION_ID + 18, "Mutual-Nil Prison"),
    "Studio 51 - Quiet Hills Set Cleared":  LocationData(BASE_LOCATION_ID + 19, "Studio 51"),
    "Studio 51 - Backstage Reached":        LocationData(BASE_LOCATION_ID + 20, "Studio 51"),
    "Mansion - Ground Floor Cleared":       LocationData(BASE_LOCATION_ID + 21, "Mansion Hideout"),
    "Mansion - Attic Reached":              LocationData(BASE_LOCATION_ID + 22, "Mansion Hideout"),
    "Chinatown - Market Cleared":           LocationData(BASE_LOCATION_ID + 23, "Chinatown"),
    "Chinatown - Rooftops Reached":         LocationData(BASE_LOCATION_ID + 24, "Chinatown"),
    "Dragon - Street Level Cleared":        LocationData(BASE_LOCATION_ID + 25, "Dragon Tape"),
    "Dragon - Dragon's Den Reached":        LocationData(BASE_LOCATION_ID + 26, "Dragon Tape"),
    "Slaughterhouse - Entry Cleared":       LocationData(BASE_LOCATION_ID + 27, "Slaughterhouse"),
    "Slaughterhouse - Camera Room Reached": LocationData(BASE_LOCATION_ID + 28, "Slaughterhouse"),
    "Bunker - Exterior Cleared":            LocationData(BASE_LOCATION_ID + 29, "Bunker"),
    "Bunker - Deep Bunker Reached":         LocationData(BASE_LOCATION_ID + 30, "Bunker"),

    # ── Boss Defeats ── IDs 82200031-82200034
    "V Defeated":            LocationData(BASE_LOCATION_ID + 31, "Studio 51"),
    "Kissyface Defeated":    LocationData(BASE_LOCATION_ID + 32, "Slaughterhouse"),
    "Headhunter Defeated":   LocationData(BASE_LOCATION_ID + 33, "Bunker"),
    "Psychiatrist Defeated": LocationData(BASE_LOCATION_ID + 34, "Psychiatrist's Office"),

    # ── Vanilla Hidden Key Spots ── IDs 82200035-82200039
    "Factory - Left Roof Corpse":        LocationData(BASE_LOCATION_ID + 35, "Factory Hideout"),
    "Hotel - Penthouse Assassination":   LocationData(BASE_LOCATION_ID + 36, "Murdower Hotel"),
    "Prison - Pacifist Suitcase":        LocationData(BASE_LOCATION_ID + 37, "Mutual-Nil Prison"),
    "Mansion - Robber's Sack":           LocationData(BASE_LOCATION_ID + 38, "Mansion Hideout"),
    "Slaughterhouse - Camera Room":      LocationData(BASE_LOCATION_ID + 39, "Slaughterhouse"),
}

from .enemy_data import ENEMY_CHECKS

# Enemy locations for Enemysanity mode (IDs 82200100 – 82200586)
enemy_location_table: Dict[str, LocationData] = {
    e.name: LocationData(e.location_id, e.region) for e in ENEMY_CHECKS
}

# Complete location table containing base checks + enemy checks
all_location_table: Dict[str, LocationData] = {
    **location_table,
    **enemy_location_table,
}

# Reverse lookup: location name → numeric ID (excludes event locations with code=None).
location_name_to_id: Dict[str, int] = {
    name: data.code for name, data in all_location_table.items() if data.code is not None
}
