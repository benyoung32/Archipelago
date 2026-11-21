from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import LocationProgressType, Region

from .data.location_data import (
    InsaniquariumLocation,
    InsaniquariumLocationData,
)

if TYPE_CHECKING:
    from . import InsaniquariumWorld


def is_location_enabled(world: InsaniquariumWorld, loc: InsaniquariumLocationData) -> bool:
    """Returns True if the given location check should be included in generation."""
    if loc.is_egg_piece_2 and world.options.egg_pieces_per_level.value < 3:
        return False
    if loc.is_egg_piece_1 and world.options.egg_pieces_per_level.value < 2:
        return False
    if loc.is_time_trial and not (world.options.include_time_trials or world.options.time_trial_required):
        return False
    if loc.is_challenge and not (world.options.include_challenge_mode or world.options.challenge_mode_required):
        return False
    if loc.is_alien and not world.options.aliensanity:
        return False
    return True


def assign_alien_regions(world: InsaniquariumWorld) -> dict[str, list[str]]:
    """
    Randomizes alien spawns across adventure tanks such that:
      - Each of the 4 tanks has 3 to 4 aliens.
      - Each alien appears in at least 2 tanks.
    Returns tank_to_aliens mapping (Tank 1-4 -> list of defeat alien location names).
    """
    tank_to_aliens: dict[str, list[str]] = {}
    alien_to_tanks: dict[InsaniquariumLocationData, list[str]] = {}

    if world.options.alien_randomization:
        tanks = ["Tank 1", "Tank 2", "Tank 3", "Tank 4"]
        alien_locs = [loc for loc in InsaniquariumLocationData if loc.is_alien]

        # All 6 possible tank pairs; each tank appears in exactly 3 pairs
        tank_pairs = [
            (tanks[i], tanks[j])
            for i in range(len(tanks))
            for j in range(i + 1, len(tanks))
        ]
        world.random.shuffle(tank_pairs)

        # 7 aliens need pairs; pick a 7th pair randomly from tank_pairs
        seventh_pair = world.random.choice(tank_pairs)
        assigned_pairs = tank_pairs + [seventh_pair]
        world.random.shuffle(assigned_pairs)
        world.random.shuffle(alien_locs)

        tank_aliens_set: dict[str, set[InsaniquariumLocationData]] = {t: set() for t in tanks}
        alien_tanks_set: dict[InsaniquariumLocationData, set[str]] = {a: set() for a in alien_locs}

        for alien, (t1, t2) in zip(alien_locs, assigned_pairs):
            tank_aliens_set[t1].add(alien)
            tank_aliens_set[t2].add(alien)
            alien_tanks_set[alien].add(t1)
            alien_tanks_set[alien].add(t2)

        # Add an extra alien to tanks with less than 4 aliens
        for t in tanks:
            if len(tank_aliens_set[t]) == 3:
                candidates = sorted(set(alien_locs) - tank_aliens_set[t], key=lambda x: x.id)
                chosen = world.random.choice(candidates)
                tank_aliens_set[t].add(chosen)
                alien_tanks_set[chosen].add(t)

        tank_to_aliens = {t: sorted(loc.location_name for loc in tank_aliens_set[t]) for t in tanks}
        alien_to_tanks = {a: sorted(alien_tanks_set[a]) for a in alien_locs}

    world.alien_regions = tank_to_aliens
    world.alien_to_tanks = alien_to_tanks
    return tank_to_aliens


def create_regions(world: InsaniquariumWorld) -> None:
    menu = Region(world.origin_region_name, world.player, world.multiworld)
    world.multiworld.regions.append(menu)

    assign_alien_regions(world)

    # Group enabled locations by region name from the location data
    locations_by_region: dict[str, dict[str, int]] = {}
    for loc in InsaniquariumLocationData:
        if not is_location_enabled(world, loc):
            continue
        # If alien randomization is active, defeat checks get dedicated sub-regions connected from each tank
        if world.options.alien_randomization and loc.is_alien:
            continue
        region_name = loc.region or world.origin_region_name
        locations_by_region.setdefault(region_name, {})[loc.location_name] = loc.id

    # Create standard regions and assign their respective locations
    regions: dict[str, Region] = {world.origin_region_name: menu}
    for region_name, locations in locations_by_region.items():
        if region_name not in regions:
            region = Region(region_name, world.player, world.multiworld)
            world.multiworld.regions.append(region)
            menu.connect(region)
            regions[region_name] = region

        regions[region_name].add_locations(locations, InsaniquariumLocation)

    # Configure progress type for bonus pet locations based on option:
    # Bonus Pet 1 through N are allowed as default locations, while the rest are filler only (excluded).
    for i in range(1, 5):
        try:
            bonus_pet_loc = world.get_location(f"Bonus Pet {i}")
            if i <= world.options.bonus_pet_locations.value:
                bonus_pet_loc.progress_type = LocationProgressType.DEFAULT
            else:
                bonus_pet_loc.progress_type = LocationProgressType.EXCLUDED
        except KeyError:
            pass

    # For alien randomization: create a sub-region for each alien check
    # and connect it from every tank the alien spawns in
    if world.options.alien_randomization:
        for loc in world.alien_to_tanks:
            if not is_location_enabled(world, loc):
                continue

            alien_region_name = f"{loc.location_name} Region"
            alien_region = Region(alien_region_name, world.player, world.multiworld)
            world.multiworld.regions.append(alien_region)
            alien_region.add_locations({loc.location_name: loc.id}, InsaniquariumLocation)
            regions[alien_region_name] = alien_region

            for tank_name in world.alien_to_tanks[loc]:
                regions[tank_name].connect(alien_region)
