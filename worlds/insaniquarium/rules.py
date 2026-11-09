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

        # TODO: review and simplify 
        # Completing a tank requires completing its final stage (Egg Piece 3 of stage 5)
        for t in range(1, 5):
            tank_complete_loc = f"Tank {t} Complete"
            stage_5_final = f"Tank {t}-5 Egg Piece 3"
            world.set_rule(
                world.get_location(tank_complete_loc),
                lambda state, final=stage_5_final: state.can_reach_location(final, world.player),
            )

        # Time trials and Challenge mode require completing their respective adventure tank
        for t in range(1, 5):
            tank_complete_loc = f"Tank {t} Complete"

            # Time trial checks
            tt_loc = f"Time Trial {t} Complete"
            try:
                location = world.get_location(tt_loc)
                world.set_rule(
                    location,
                    lambda state, tc=tank_complete_loc: state.can_reach_location(tc, world.player),
                )
            except KeyError:
                pass

            # TODO: review and simplify this section. challenge location needs to be added
            # Challenge mode checks
            challenge_loc_candidates = [
                f"Challenge Mode {t} Complete",
                f"Challenge {t} Complete",
                f"Tank {t} Challenge Complete",
            ]
            for ch_name in challenge_loc_candidates:
                try:
                    location = world.get_location(ch_name)
                    world.set_rule(
                        location,
                        lambda state, tc=tank_complete_loc: state.can_reach_location(tc, world.player),
                    )
                except KeyError:
                    pass

        # Completion Condition:
        # Completing all 4 tanks is always a victory condition. Extra conditions are configured via options.
        def victory_condition(state) -> bool:
            # All 4 tanks are always required
            if not (
                state.can_reach_location("Tank 1 Complete", world.player)
                and state.can_reach_location("Tank 2 Complete", world.player)
                and state.can_reach_location("Tank 3 Complete", world.player)
                and state.can_reach_location("Tank 4 Complete", world.player)
            ):
                return False

            # Cyrax (Tank 5 boss) requirement
            if bool(getattr(world.options, "cyrax_required", True)):
                if not state.can_reach_location("Cyrax", world.player):
                    return False

            # Time Trials requirement
            if bool(getattr(world.options, "time_trial_required", False)):
                for t in range(1, 5):
                    tt_loc = f"Time Trial {t} Complete"
                    if not state.can_reach_location(tt_loc, world.player):
                        return False

            # Challenge Mode requirement (if challenge mode checks are present)
            if bool(getattr(world.options, "challenge_mode_required", False)):
                for t in range(1, 5):
                    ch_locs = [
                        loc_name for loc_name in [
                            f"Challenge Mode {t} Complete",
                            f"Challenge {t} Complete",
                            f"Tank {t} Challenge Complete",
                        ]
                        if loc_name in world.location_name_to_id
                    ]
                    if ch_locs and not any(state.can_reach_location(loc, world.player) for loc in ch_locs):
                        return False

            return True

        world.multiworld.completion_condition[world.player] = victory_condition
