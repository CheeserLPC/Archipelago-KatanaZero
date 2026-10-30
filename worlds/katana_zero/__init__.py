from BaseClasses import ItemClassification, Tutorial
from worlds.AutoWorld import World, WebWorld

from .Items import KatanaZeroItem, item_table, get_filler_item_names, get_trap_item_names
from .Locations import location_table, all_location_table, location_name_to_id
from .Options import KatanaZeroOptions

# Register Launcher Component for the Archipelago Launcher UI
try:
    from . import Components as components
except ImportError:
    pass


class KatanaZeroWebWorld(WebWorld):
    theme = "dirt"
    tutorials = [Tutorial(
        tutorial_name="Setup Guide",
        description="A guide to setting up the Katana ZERO Archipelago randomizer.",
        language="English",
        file_name="setup_en.md",
        link="guide/en",
        authors=["KatanaZeroAP"],
    )]


class KatanaZeroWorld(World):
    """
    Katana ZERO is a stylish neo-noir action platformer featuring
    instant-death combat and time manipulation. This randomizer
    scatters VHS Tapes, Mechanic Shards, Government Lab Keys, and
    Swords across the multiworld.
    """

    game = "Katana ZERO"
    web = KatanaZeroWebWorld()
    options_dataclass = KatanaZeroOptions
    options: KatanaZeroOptions

    item_name_to_id = {name: data.code for name, data in item_table.items() if data.code is not None}
    location_name_to_id = location_name_to_id

    def get_starting_tape_name(self) -> str:
        tape_map = {
            0: "Tape: Factory",
            1: "Tape: Hotel",
            2: "Tape: Club",
            3: "Tape: Prison",
            4: "Tape: Studio 51",
            5: "Tape: Mansion",
            6: "Tape: Chinatown",
            7: "Tape: Dragon",
            8: "Tape: Slaughterhouse",
            9: "Tape: Bunker",
        }
        val = self.options.starting_tape.value
        if val == 10:  # random
            return self.random.choice(list(tape_map.values()))
        return tape_map.get(val, "Tape: Factory")

    def create_regions(self) -> None:
        from .Regions import create_regions
        create_regions(self)

    def create_items(self) -> None:
        # 1. Determine and grant starting tape to player
        starting_tape_name = self.get_starting_tape_name()
        self.multiworld.push_precollected(self.create_item(starting_tape_name))

        # 2. Create all remaining progression and useful items
        pool = []
        for item_name, data in item_table.items():
            if item_name == starting_tape_name:
                continue  # already precollected as starting item
            if data.classification in (ItemClassification.progression, ItemClassification.useful):
                # Skip swords if shuffle_swords is off
                if data.classification == ItemClassification.useful and not self.options.shuffle_swords:
                    continue
                for _ in range(data.count):
                    pool.append(self.create_item(item_name))

        # 3. Calculate remaining slots to fill all locations
        total_locations = len(list(self.multiworld.get_locations(self.player)))
        remaining = total_locations - len(pool)

        # 4. Fill remaining slots with traps and filler based on trap_percentage
        trap_names = get_trap_item_names()
        filler_names = get_filler_item_names()
        trap_count = int(remaining * (self.options.trap_percentage.value / 100))
        filler_count = remaining - trap_count

        for i in range(trap_count):
            trap_name = trap_names[i % len(trap_names)]
            pool.append(self.create_item(trap_name))

        for i in range(filler_count):
            filler_name = filler_names[i % len(filler_names)]
            pool.append(self.create_item(filler_name))

        self.multiworld.itempool += pool

    def create_item(self, name: str) -> "KatanaZeroItem":
        return KatanaZeroItem(name, item_table[name].classification, item_table[name].code, self.player)

    def set_rules(self) -> None:
        from .Rules import set_rules
        set_rules(self)

    def fill_slot_data(self) -> dict:
        return {
            "goal": self.options.goal.value,
            "starting_tape": self.get_starting_tape_name(),
            "required_tapes": self.options.required_tapes.value,
            "shuffle_swords": self.options.shuffle_swords.value,
            "enemysanity": self.options.enemysanity.value,
            "trap_percentage": self.options.trap_percentage.value,
            "death_link": self.options.death_link.value,
            "death_link_amnesty": self.options.death_link_amnesty.value,
            "randomize_music": int(bool(self.options.randomize_music.value)),
            "randomize_sfx": int(bool(self.options.randomize_sfx.value)),
            "audio_seed": self.random.randint(0, 0x7FFFFFFF),
        }

    def get_filler_item_name(self) -> str:
        return self.random.choice(get_filler_item_names())
