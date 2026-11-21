from __future__ import annotations

from typing import Any

from BaseClasses import Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World

GAME_NAME = "Insaniquarium Deluxe"
WORLD_VERSION = "world_version"

from . import regions
from .data import item_data, location_data
from .data.item_data import InsaniquariumItem, ITEM_DATA
from .data.location_data import InsaniquariumLocationData
from .options import InsaniquariumOptions, StartingTank, insaniquarium_option_groups
from .rules import InsaniquariumRules


class InsaniquariumWebWorld(WebWorld):
    theme = "ocean"
    option_groups = insaniquarium_option_groups
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to playing Insaniquarium Deluxe with Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["benyoung32", "dmwever"],
        )
    ]


class InsaniquariumWorld(World):
    """Insaniquarium Deluxe: feed your fish, fight off aliens, collect the pets."""

    game = GAME_NAME
    options_dataclass = InsaniquariumOptions
    options: InsaniquariumOptions
    web = InsaniquariumWebWorld()

    item_name_to_id = item_data.item_name_to_id
    location_name_to_id = location_data.location_name_to_id
    item_name_groups = item_data.item_name_groups

    origin_region_name = "Menu"

    starting_tank_unlock: str = ""
    starting_item_names: list[str] = []
    alien_regions: dict[str, list[str]] = {}
    alien_to_tanks: dict[InsaniquariumLocationData, list[str]] = {}
    bonus_starting_guppies_created: int = 0

    def generate_early(self) -> None:
        """
        Pre-places starting items before the rest of generation to keep things in logic and
        duplicates out of the item pool.
        """
        self.bonus_starting_guppies_created = 0
        tank_map = {
            StartingTank.option_tank_1: item_data.TANK_1_UNLOCK,
            StartingTank.option_tank_2: item_data.TANK_2_UNLOCK,
            StartingTank.option_tank_3: item_data.TANK_3_UNLOCK,
            StartingTank.option_tank_4: item_data.TANK_4_UNLOCK,
        }
        self.starting_tank_unlock = tank_map.get(
            self.options.starting_tank.value,
            self.random.choice(list(tank_map.values())),
        )
        self.starting_item_names = [self.starting_tank_unlock]
        self.multiworld.push_precollected(self.create_item(self.starting_tank_unlock))

        # If time trials or challenge mode are required to win, ensure their checks are included
        if self.options.time_trial_required and not self.options.include_time_trials:
            self.options.include_time_trials.value = 1
        if self.options.challenge_mode_required and not self.options.include_challenge_mode:
            self.options.include_challenge_mode.value = 1

    def create_regions(self) -> None:
        """Method for creating and connecting regions for the World."""
        regions.create_regions(self)

    def create_items(self) -> None:
        """
        Method for creating and submitting items to the itempool. Items and Regions must *not* be created and submitted
        to the MultiWorld after this step.
        """
        itempool: list[InsaniquariumItem] = []
        
        # Add all items from the item pool
        for name, item in ITEM_DATA.items():
            for _ in range(item.quantity):
                # ignore starting items
                if name not in self.starting_item_names:
                    itempool.append(self.create_item(name))

        # Add pet slots
        for _ in range(self.options.pet_slot_items.value):
            itempool.append(self.create_item("Pet Slot Upgrade"))

        # Check location count
        active_locations_count = len(self.multiworld.get_unfilled_locations(self.player))
        if len(itempool) > active_locations_count:
            raise OptionError(
                f"{self.player_name}'s {self.game} world has too few locations ({active_locations_count}) "
                f"to place all required items ({len(itempool)})."
            )

        # Fill remaining slots with filler or traps
        for _ in range(active_locations_count - len(itempool)):
            itempool.append(self.get_filler_item())

        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> InsaniquariumItem:
        data = ITEM_DATA[name]
        return InsaniquariumItem(name, data.classification, data.id, self.player)

    def get_filler_item_name(self) -> str:
        trap_chance = self.options.trap_chance.value

        traps: dict[str, int] = {
            item_data.TRAP_ALIEN_ATTACK: self.options.alien_attack_trap_weight.value,
            item_data.TRAP_FAMINE: self.options.famine_trap_weight.value,
        }
        
        filler: dict[str, int] = {
            item_data.STARTING_MONEY: self.options.bonus_money_weight.value,
            item_data.BONUS_LEVEL_TICKET: self.options.bonus_level_ticket_weight.value,
            item_data.BONUS_STARTING_GUPPY: 
            self.options.bonus_money_weight.value + self.options.bonus_level_ticket_weight.value,
        }

        # If we've already placed all bonus starting guppies, remove them from the pool
        if self.bonus_starting_guppies_created >= self.options.bonus_starting_guppies.value:
            filler[item_data.BONUS_STARTING_GUPPY] = 0
        
        # Determine if pulling from trap or filler pool
        if sum(traps.values()) > 0 and self.random.randint(1, 100) <= trap_chance:
            pool = traps
        elif sum(filler.values()) > 0:
            pool = filler
        else:
            return item_data.STARTING_MONEY

        chosen = self.random.choices(
            list(pool.keys()),
            weights=list(pool.values()),
            k=1,
        )[0]
        if chosen == item_data.BONUS_STARTING_GUPPY:
            self.bonus_starting_guppies_created += 1
        return chosen

    def get_filler_item(self) -> InsaniquariumItem:
        return self.create_item(self.get_filler_item_name())

    def set_rules(self) -> None:
        InsaniquariumRules(self).set_rules()

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            WORLD_VERSION: self.world_version.as_simple_string(),
            "starting_tank_unlock": self.starting_tank_unlock,
            "egg_pieces_per_level": self.options.egg_pieces_per_level.value,
            "cyrax_required": bool(self.options.cyrax_required.value),
            "time_trial_required": bool(self.options.time_trial_required.value),
            "challenge_mode_required": bool(self.options.challenge_mode_required.value),
            "upgrade_availability": self.options.upgrade_availability.value,
            "aliensanity": bool(self.options.aliensanity.value),
            "starting_pet_slots": self.options.starting_pet_slots.value,
            "bonus_pet_locations": self.options.bonus_pet_locations.value,
            "death_link": bool(self.options.death_link.value),
            "death_link_amnesty": self.options.death_link_amnesty.value,
            "death_link_effect": self.options.death_link_effect.value,
            "alien_randomized": bool(self.options.alien_randomization.value),
            "alien_randomization": self.alien_regions,
        }


# Ensure world_version is loaded from archipelago.json even when imported directly
try:
    import json
    import pkgutil
    from Utils import tuplize_version

    _manifest_raw = pkgutil.get_data(__name__, "archipelago.json")
    if _manifest_raw:
        _manifest = json.loads(_manifest_raw.decode("utf-8"))
        if "world_version" in _manifest:
            InsaniquariumWorld.world_version = tuplize_version(_manifest["world_version"])
except Exception:
    pass

