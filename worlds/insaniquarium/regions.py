from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from BaseClasses import Region

from .data.item_data import InsaniquariumItem, VICTORY_ITEM_NAME
from .location_data import (
    InsaniquariumLocation,
    InsaniquariumLocationData,
    VICTORY_LOCATION_NAME,
)

if TYPE_CHECKING:
    from . import InsaniquariumWorld


def is_location_enabled(world: InsaniquariumWorld, loc: InsaniquariumLocationData) -> bool:
    name = loc.location_name
    pieces = int(getattr(world.options, "egg_pieces_per_level", 3))

    if "Egg Piece 2" in name and pieces < 3:
        return False
    if "Egg Piece 1" in name and pieces < 2:
        return False

    if name.startswith("Time Trial ") and not bool(getattr(world.options, "include_time_trials", True)):
        return False

    if name.startswith("Bonus Pet ") and not bool(getattr(world.options, "include_bonus_pets", True)):
        return False

    return True


def create_regions(world: InsaniquariumWorld) -> None:
    menu = Region(world.origin_region_name, world.player, world.multiworld)
    world.multiworld.regions.append(menu)

    # Group enabled locations by region name from the location data
    locations_by_region: dict[str, dict[str, int]] = {}
    for loc in InsaniquariumLocationData:
        if not is_location_enabled(world, loc):
            continue
        region_name = loc.region or world.origin_region_name
        locations_by_region.setdefault(region_name, {})[loc.location_name] = loc.id

    # Create regions and assign their respective locations
    regions: dict[str, Region] = {world.origin_region_name: menu}
    for region_name, locations in locations_by_region.items():
        if region_name not in regions:
            region = Region(region_name, world.player, world.multiworld)
            world.multiworld.regions.append(region)
            menu.connect(region)
            regions[region_name] = region

        regions[region_name].add_locations(locations, InsaniquariumLocation)

    # Victory event placed on Menu
    menu.add_event(
        VICTORY_LOCATION_NAME,
        VICTORY_ITEM_NAME,
        location_type=InsaniquariumLocation,
        item_type=InsaniquariumItem,
    )


# Compatibility alias in case of `from .regions import regions`
regions = sys.modules[__name__]
