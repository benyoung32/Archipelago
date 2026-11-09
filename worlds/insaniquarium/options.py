from __future__ import annotations

from dataclasses import dataclass

from Options import (
    Choice,
    DefaultOnToggle,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)


class StartingTank(Choice):
    """Choose which tank you start with.
    Random: A random tank unlock (Tank 1 through 4) is given as starting inventory.
    Tank 1 - 4: Begin with the selected tank unlocked."""
    display_name = "Starting Tank"
    option_random = 0
    option_tank_1 = 1
    option_tank_2 = 2
    option_tank_3 = 3
    option_tank_4 = 4
    default = 0

# TODO: add starting pets option. the player could choose to start with a random selection of pets unlocked, 
# how many starting slots to have, max number of slots  

# TODO: add mid level check option. 
# 0 - none
# 1 - one check when food upgrades are unlocked per level
# 2 - one check when the egg is unlocked per level (plus above)

class EggPiecesPerLevel(Range):
    """Controls how many egg purchases in each level provide an Archipelago check.
    1: Only the final egg piece is a check (20 level checks).
    2: Egg pieces 1 and 3 are checks (40 level checks).
    3: All 3 egg pieces in every level are checks (60 level checks)."""
    display_name = "Egg Pieces per Level"
    range_start = 1
    range_end = 3
    default = 3

"Completing all 4 tanks is always a victory condition. Add extra conditions below"

class CyraxRequired(Toggle):
    "Control if cyrax is necessary to win"
    display_name = "Cyrax Required"
    default = True

class TimeTrialRequired(Toggle):
    "Control if time trials are necessary to win"
    display_name = "Time Trials Required"
    default = False
class ChallengeModeRequired(Toggle):
    "Control if challenge mode is necessary to win"
    display_name = "Challenge Mode Required"
    default = False    

# TODO: potentially add virtual tank win condition

class UpgradeAvailbility(Choice):
    """Controls when received upgrade items are available during each level
    0: Upgrades are immediately applied once recevied
    1: Upgrades are available for free once received
    2: Upgrades are available for normal price once received"""
    display_name = "Upgrade Availability"
    option_always = 0
    option_free = 1
    option_normal_price = 2
    default = 1

# TODO: add more bonus items and options for bonus starting money. 
# bonus shells for unlocking bonus pets can be an option
class BonusShellsWeight(Range):
    """
    This is summed with other bonus item weights to determine the probability of receiving bonus money.
    """
    display_name = "Bonus Shells Weight"
    range_start = 0
    range_end = 100
    default = 0

class BonusMoneyWeight(Range):
    """
    This is summed with other bonus item weights to determine the probability of receiving bonus money.
    """
    display_name = "Bonus Money Weight"
    range_start = 1
    range_end = 100
    default = 1

# TODO: add option for altering bonus pet cost. by default they are 20k shells x 4 
# this will need to be added to slot_data.json 
class IncludeTimeTrials(DefaultOnToggle):
    """Include 4 Time Trial completion checks in the randomizer pool."""
    display_name = "Include Time Trials"

class TrapChance(Range):
    """Percentage chance to replace non-progression filler items with traps."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


# TODO: aliensanity option
# defeating aliens for the first time is a check
class Aliensanity(Toggle):
    """Control if defeating aliens for the first time is a check"""
    display_name = "Aliensanity"
    default = False

# TODO: alien randomzier
# each level chooses from the alien pool randomly (maybe there needs to be a difficulty rating)

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
    cyrax_required: CyraxRequired
    time_trial_required: TimeTrialRequired
    challenge_mode_required: ChallengeModeRequired
    upgrade_availability: UpgradeAvailbility
    bonus_shells_weight: BonusShellsWeight
    bonus_money_weight: BonusMoneyWeight
    include_time_trials: IncludeTimeTrials
    aliensanity: Aliensanity
    trap_chance: TrapChance
    alien_attack_trap_weight: AlienAttackTrapWeight
    famine_trap_weight: FamineTrapWeight
    start_inventory_from_pool: StartInventoryPool
