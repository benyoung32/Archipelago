from __future__ import annotations

from dataclasses import dataclass

from Options import (
    Choice,
    DefaultOnToggle,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
)


class StartingTank(Choice):
    """Choose which tank you start with.
    Random: A random tank unlock (Tank 1 through 4) is given as starting inventory.
    Tank 1 - 4: Explicitly begin with the selected tank unlocked."""
    display_name = "Starting Tank"
    option_random = 0
    option_tank_1 = 1
    option_tank_2 = 2
    option_tank_3 = 3
    option_tank_4 = 4
    default = 0


class EggPiecesPerLevel(Range):
    """Controls how many egg purchases in each level provide an Archipelago check.
    1: Only the 3rd egg piece (completing the level) is a check (20 level checks).
    2: Egg pieces 1 and 3 are checks (40 level checks).
    3: All 3 egg purchases in every level are checks (60 level checks)."""
    display_name = "Egg Pieces per Level"
    range_start = 1
    range_end = 3
    default = 3


class Goal(Choice):
    """Set the completion goal for the randomizer seed.
    Defeat Cyrax: Defeat the final boss in Tank 5 (unlocked after beating Tanks 1-4).
    All Tanks: Complete the first four adventure tanks (Tank 1 through 4 Complete).
    All Tanks & Bonus Pets: Complete all 4 tanks and collect all 4 Bonus Pets.
    Full Completion: Defeat Cyrax and collect all 4 Bonus Pets."""
    display_name = "Goal"
    option_defeat_cyrax = 0
    option_all_tanks = 1
    option_all_tanks_and_bonus = 2
    option_full_completion = 3
    default = 0


class IncludeTimeTrials(DefaultOnToggle):
    """Include the 4 Time Trial completion checks in the randomizer pool."""
    display_name = "Include Time Trials"


class IncludeBonusPets(DefaultOnToggle):
    """Include the 4 Bonus Pet checks in the randomizer pool."""
    display_name = "Include Bonus Pets"


class TrapChance(Range):
    """Percentage chance to replace non-progression filler items with traps."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class AlienAttackTrapWeight(Range):
    """Relative weight of Alien Attack Traps when a trap is selected."""
    display_name = "Alien Attack Trap Weight"
    range_start = 0
    range_end = 100
    default = 50


class FamineTrapWeight(Range):
    """Relative weight of Famine Traps when a trap is selected."""
    display_name = "Famine Trap Weight"
    range_start = 0
    range_end = 100
    default = 50


@dataclass
class InsaniquariumOptions(PerGameCommonOptions):
    starting_tank: StartingTank
    egg_pieces_per_level: EggPiecesPerLevel
    goal: Goal
    include_time_trials: IncludeTimeTrials
    include_bonus_pets: IncludeBonusPets
    trap_chance: TrapChance
    alien_attack_trap_weight: AlienAttackTrapWeight
    famine_trap_weight: FamineTrapWeight
    start_inventory_from_pool: StartInventoryPool
