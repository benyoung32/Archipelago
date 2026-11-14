from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from BaseClasses import Region

from .data.location_data import (
    InsaniquariumLocation,
    InsaniquariumLocationData,
)

if TYPE_CHECKING:
    from . import InsaniquariumWorld


def is_location_enabled(world: InsaniquariumWorld, loc: InsaniquariumLocationData) -> bool:
    name = loc.location_name
    # included egg pieces
    pieces = int(getattr(world.options, "egg_pieces_per_level", 3))

    if "Egg Piece 2" in name and pieces < 3:
        return False
    if "Egg Piece 1" in name and pieces < 2:
        return False
    
    # include time trial and challenge mode 
    # if time trials or challenge mode are required to win, always include their locations
    time_trials_enabled = bool(getattr(world.options, "include_time_trials", True)) or bool(getattr(world.options, "time_trial_required", False))
    if name.startswith("Time Trial ") and not time_trials_enabled:
        return False

    challenge_enabled = bool(getattr(world.options, "include_challenge_mode", True)) or bool(getattr(world.options, "challenge_mode_required", False))
    if (name.startswith("Challenge ") or name.startswith("Challenge Mode ")) and not challenge_enabled:
        return False
    
    # include bonus pet locations
    if name.startswith("Bonus Pet "):
        bonus_pet_opt = getattr(world.options, "bonus_pet_locations")    
        try:
            pet_index = int(name.rsplit(" ", 1)[-1])
        except ValueError:
            pet_index = 1
        if pet_index > int(bonus_pet_opt.value):
            return False
    
    # aliensanity 
    if name.startswith("Defeat ") and not bool(getattr(world.options, "aliensanity", True)):
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


# Compatibility alias in case of `from .regions import regions`
regions = sys.modules[__name__]
