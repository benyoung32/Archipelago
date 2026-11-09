from __future__ import annotations

from typing import Any

from BaseClasses import Item, Location
from Options import OptionError
from worlds.AutoWorld import World

GAME_NAME = "Insaniquarium Deluxe"
WORLD_VERSION = "world_version"

from .data import item_data, location_data
from .container import InsaniquariumContainer
from .data.item_data import InsaniquariumItem, ITEM_DATA, InsaniquariumItemData
from .options import InsaniquariumOptions, StartingTank
from .regions import regions
from .rules import InsaniquariumRules


class InsaniquariumWorld(World):
    """Insaniquarium Deluxe: feed your fish, fight off aliens, collect the pets."""

    game = GAME_NAME
    options_dataclass = InsaniquariumOptions
    options: InsaniquariumOptions

    item_name_to_id = item_data.item_name_to_id
    location_name_to_id = location_data.location_name_to_id
    item_name_groups = item_data.item_name_groups

    origin_region_name = "Menu"

    starting_tank_unlock: str = ""
    starting_item_names: list[str] = []

    def generate_early(self) -> None:
        """
        This method pre-places starting items before the rest of generation to keep things in logic and
        duplicates out of the item pool. 
        """
        tank_map = {
            StartingTank.option_tank_1: item_data.TANK_1_UNLOCK,
            StartingTank.option_tank_2: item_data.TANK_2_UNLOCK,
            StartingTank.option_tank_3: item_data.TANK_3_UNLOCK,
            StartingTank.option_tank_4: item_data.TANK_4_UNLOCK,
        }
        choice = getattr(self.options, "starting_tank", StartingTank.default)
        if choice in tank_map:
            self.starting_tank_unlock = tank_map[choice]
        else:
            self.starting_tank_unlock = self.random.choice(list(tank_map.values()))
        
        self.starting_item_names.append(self.starting_tank_unlock)

        self.multiworld.push_precollected(self.create_item(self.starting_tank_unlock))

        # If time trials are required to beat the game, ensure their check locations are in the pool
        if bool(getattr(self.options, "time_trial_required", False)) and not bool(getattr(self.options, "include_time_trials", True)):
            self.options.include_time_trials.value = 1

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
        trap_chance = int(getattr(self.options, "trap_chance", 0))

        traps: dict[str, int] = {
            item_data.TRAP_ALIEN_ATTACK: int(getattr(self.options, "alien_attack_trap_weight", 50)),
            item_data.TRAP_FAMINE: int(getattr(self.options, "famine_trap_weight", 50)),
        }
        
        filler: dict[str, int] = {
            item_data.STARTING_MONEY:   int(getattr(self.options, "bonus_money_weight", 1)),
            item_data.BONUS_SHELLS:     int(getattr(self.options, "bonus_shells_weight", 0)),
        }

        # determine if pulling from trap or filler pool
        pool = traps if (sum(traps.values()) > 0 and self.random.randint(1, 100) <= trap_chance) else filler 
        
        return self.random.choices(
            list(pool.keys()),
            weights = list(pool.values()),
            k = 1
        )[0]

    def get_filler_item(self) -> InsaniquariumItem:
        return self.create_item(self.get_filler_item_name())

    def set_rules(self) -> None:
        InsaniquariumRules(self).set_rules()

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            WORLD_VERSION: self.world_version.as_simple_string(),
            "starting_tank_unlock": self.starting_tank_unlock,
            "egg_pieces_per_level": int(self.options.egg_pieces_per_level),
            "cyrax_required": bool(self.options.cyrax_required),
            "time_trial_required": bool(self.options.time_trial_required),
            "challenge_mode_required": bool(self.options.challenge_mode_required),
            "upgrade_availability": int(self.options.upgrade_availability),
            "aliensanity": bool(self.options.aliensanity),
        }

    def generate_output(self, output_directory: str) -> None:
        container = InsaniquariumContainer(
            output_directory=output_directory,
            player=self.player,
            player_name=self.multiworld.get_file_safe_player_name(self.player),
            world=self,
        )
        container.write()

