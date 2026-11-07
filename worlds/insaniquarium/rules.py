from __future__ import annotations

from typing import TYPE_CHECKING

from .data.item_data import (
    TANK_1_UNLOCK,
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
)

from .options import Goal

if TYPE_CHECKING:
    from . import InsaniquariumWorld


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

        # Cyrax requires completing all 4 adventure tanks
        tank_5_entrance = world.get_entrance("Menu -> Tank 5")
        world.set_rule(
            tank_5_entrance,
            lambda state: state.can_reach_location("Tank 1 Complete", world.player)
            and state.can_reach_location("Tank 2 Complete", world.player)
            and state.can_reach_location("Tank 3 Complete", world.player)
            and state.can_reach_location("Tank 4 Complete", world.player),
        )

        # Completing a tank requires completing its final stage (Egg Piece 3 of stage 5)
        for t in range(1, 4):
            tank_complete_loc = f"Tank {t} Complete"
            stage_5_final = f"Tank {t}-5 Egg Piece 3"
            world.set_rule(
                world.get_location(tank_complete_loc),
                lambda state, final=stage_5_final: state.can_reach_location(final, world.player),
            )
        # TODO: see options.py for goal rework
        # Set completion condition based on the selected goal
        goal = getattr(world.options, "goal", Goal.default)

        if goal == Goal.option_all_tanks:
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location("Tank 1 Complete", world.player)
                and state.can_reach_location("Tank 2 Complete", world.player)
                and state.can_reach_location("Tank 3 Complete", world.player)
                and state.can_reach_location("Tank 4 Complete", world.player)
            )
        elif goal == Goal.option_all_tanks_and_bonus:
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location("Tank 1 Complete", world.player)
                and state.can_reach_location("Tank 2 Complete", world.player)
                and state.can_reach_location("Tank 3 Complete", world.player)
                and state.can_reach_location("Tank 4 Complete", world.player)
                and all(state.can_reach_location(f"Bonus Pet {b}", world.player) for b in range(1, 5))
            )
        elif goal == Goal.option_full_completion:
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location("Cyrax", world.player)
                and all(state.can_reach_location(f"Bonus Pet {b}", world.player) for b in range(1, 5))
            )
        else:
            # Default: Goal.option_defeat_cyrax
            world.multiworld.completion_condition[world.player] = (
                lambda state: state.can_reach_location("Cyrax", world.player)
            )