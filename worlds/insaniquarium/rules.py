from __future__ import annotations

from typing import TYPE_CHECKING

from .data.item_data import (
    TANK_1_UNLOCK,
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
)

if TYPE_CHECKING:
    from . import InsaniquariumWorld

ALL_TANK_UNLOCKS = {
    TANK_1_UNLOCK,
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
}


class InsaniquariumRules:
    """Applies logic to this world's regions, locations, and completion condition."""

    def __init__(self, world: InsaniquariumWorld) -> None:
        self.world = world

    def set_rules(self) -> None:
        world = self.world

        # Tank 1-4 entrances are locked behind their respective tank unlocks
        tank_unlocks = {
            "Tank 1": TANK_1_UNLOCK,
            "Tank 2": TANK_2_UNLOCK,
            "Tank 3": TANK_3_UNLOCK,
            "Tank 4": TANK_4_UNLOCK,
        }

        for tank, item_name in tank_unlocks.items():
            entrance = world.get_entrance(f"Menu -> {tank}")
            world.set_rule(entrance, lambda state, item=item_name: state.has(item, world.player))

        # Tank 5 (Cyrax) requires having unlocked all 4 adventure tanks
        tank_5_entrance = world.get_entrance("Menu -> Tank 5")
        world.set_rule(
            tank_5_entrance,
            lambda state: state.has_all(ALL_TANK_UNLOCKS, world.player),
        )

        # Completion Condition:
        # Completing all 4 tanks is always a victory condition. Extra conditions are configured via options.
        def victory_condition(state) -> bool:
            # All 4 tanks are always required
            if not state.has_all(ALL_TANK_UNLOCKS, world.player):
                return False

            # Cyrax (Tank 5 boss) requirement
            if world.options.cyrax_required:
                if not state.can_reach_location("Cyrax", world.player):
                    return False

            # Time Trials requirement (Time Trials 1-4)
            if world.options.time_trial_required:
                for t in range(1, 5):
                    if not state.can_reach_location(f"Time Trial {t} Complete", world.player):
                        return False

            # Challenge Mode requirement (Challenges 1-4)
            if world.options.challenge_mode_required:
                for t in range(1, 5):
                    if not state.can_reach_location(f"Challenge {t} Complete", world.player):
                        return False

            return True

        world.multiworld.completion_condition[world.player] = victory_condition
