from __future__ import annotations

from typing import Any

from BaseClasses import Item, Location
from worlds.AutoWorld import World

GAME_NAME = "Insaniquarium Deluxe"
WORLD_VERSION = "world_version"

from .data import item_data, location_data
from .container import InsaniquariumContainer
from .data.item_data import InsaniquariumItem, ITEM_DATA
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

    def generate_early(self) -> None:
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

        self.multiworld.push_precollected(self.create_item(self.starting_tank_unlock))

    def create_regions(self) -> None:
        """Method for creating and connecting regions for the World."""
        regions.create_regions(self)

    def create_items(self) -> None:
        """
        Method for creating and submitting items to the itempool. Items and Regions must *not* be created and submitted
        to the MultiWorld after this step.
        """
        itempool: list[InsaniquariumItem] = []

        # 1. Progression items: Tank Unlocks (minus starting precollected tank)
        tank_unlocks = [
            item_data.TANK_1_UNLOCK,
            item_data.TANK_2_UNLOCK,
            item_data.TANK_3_UNLOCK,
            item_data.TANK_4_UNLOCK,
        ]
        for name in tank_unlocks:
            if name != self.starting_tank_unlock:
                itempool.append(self.create_item(name))

        # 2. Upgrades
        upgrades = (
            [item_data.WEAPON_UPGRADE] * ITEM_DATA[item_data.WEAPON_UPGRADE].quantity
            + [item_data.FOOD_QUALITY] * ITEM_DATA[item_data.FOOD_QUALITY].quantity
            + [item_data.PET_SLOT] * ITEM_DATA[item_data.PET_SLOT].quantity
            + [item_data.FOOD_QUANTITY] * ITEM_DATA[item_data.FOOD_QUANTITY].quantity
        )

        # 3. All 24 Pets
        pets = [
            item_data.STINKY, item_data.NIKO, item_data.ITCHY, item_data.PREGO,
            item_data.ZORF, item_data.CLYDE, item_data.VERT, item_data.RUFUS,
            item_data.MERYL, item_data.WADSWORTH, item_data.SEYMOUR, item_data.SHRAPNEL,
            item_data.GUMBO, item_data.BLIP, item_data.RHUBARB, item_data.NIMBUS,
            item_data.AMP, item_data.GASH, item_data.ANGIE, item_data.PRESTO,
            item_data.BRINKLEY, item_data.NOSTRADAMUS, item_data.STANLEY, item_data.WALTER,
        ]

        active_locations_count = len(self.multiworld.get_unfilled_locations(self.player))
        # TODO: an error should be logged here if the amount of necessary items is > active locations 
        # potentially these items should be randomly precollected or generation should just fail
        # this check might have to happen in generate early
        
        for item_name in upgrades:
            if len(itempool) < active_locations_count:
                itempool.append(self.create_item(item_name))

        for pet_name in pets:
            if len(itempool) < active_locations_count:
                itempool.append(self.create_item(pet_name))

        # 4. Fill remaining slots with filler or traps
        for _ in range(active_locations_count - len(itempool)):
            itempool.append(self.get_filler_item())

        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> InsaniquariumItem:
        data = ITEM_DATA[name]
        return InsaniquariumItem(name, data.classification, data.id, self.player)

    def get_filler_item_name(self) -> str:
        trap_chance = int(getattr(self.options, "trap_chance", 0))
        alien_weight = int(getattr(self.options, "alien_attack_trap_weight", 50))
        famine_weight = int(getattr(self.options, "famine_trap_weight", 50))
        if trap_chance > 0 and (alien_weight + famine_weight > 0) and self.random.randint(1, 100) <= trap_chance:
            return self.random.choices(
                [item_data.TRAP_ALIEN_ATTACK, item_data.TRAP_FAMINE],
                weights=[alien_weight, famine_weight],
                k=1,
            )[0]
        return item_data.STARTING_MONEY

    def get_filler_item(self) -> InsaniquariumItem:
        return self.create_item(self.get_filler_item_name())

    def set_rules(self) -> None:
        InsaniquariumRules(self).set_rules()

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            WORLD_VERSION: self.world_version.as_simple_string(),
            "starting_tank_unlock": self.starting_tank_unlock,
            "goal": int(self.options.goal),
            "egg_pieces_per_level": int(self.options.egg_pieces_per_level),
        }

    def generate_output(self, output_directory: str) -> None:
        container = InsaniquariumContainer(
            output_directory=output_directory,
            player=self.player,
            player_name=self.multiworld.get_file_safe_player_name(self.player),
            world=self,
        )
        container.write()

