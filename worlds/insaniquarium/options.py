from __future__ import annotations

from dataclasses import dataclass

from Options import (
    Choice,
    DeathLink as BaseDeathLink,
    DefaultOnToggle,
    OptionGroup,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)

class StartingTank(Choice):
    """Choose which tank you start with.
    Randomized: A random tank unlock (Tank 1 through 4) is given as starting inventory.
    Tank 1 - 4: Begin with the selected tank unlocked."""
    display_name = "Starting Tank"
    option_randomized = 0
    option_tank_1 = 1
    option_tank_2 = 2
    option_tank_3 = 3
    option_tank_4 = 4
    default = 0

class StartingPetSlots(Range):
    """
    Choose how many pet slots to start with.
    """
    display_name = "Starting Pet Slots"
    range_start = 0
    range_end = 24
    default = 0

class PetSlotItems(Range):
    """
    Choose how many unlockable pet slots are available as items.
    Combined with the above option, the total number of pet slots in the game will be
    Starting Pet Slots + Pet Slot Items 
    """
    display_name = "Pet Slot Items"
    range_start = 0
    range_end = 24
    default = 3


class EggPiecesPerLevel(Range):
    """Choose how many egg purchases in each level provide an Archipelago check.
    2: Egg pieces 1 and 3 are checks (40 level checks).
    3: All 3 egg pieces in every level are checks (60 level checks)."""
    display_name = "Egg Pieces per Level"
    range_start = 2
    range_end = 3
    default = 3


class CyraxRequired(DefaultOnToggle):
    "Choose if Cyrax is necessary to win."
    display_name = "Cyrax Required"

class TimeTrialRequired(Toggle):
    "Choose if time trials are necessary to win."
    display_name = "Time Trials Required"

class ChallengeModeRequired(Toggle):
    "Choose if challenge mode is necessary to win."
    display_name = "Challenge Mode Required"


class BonusPetLocations(Range):
    """Choose how many bonus pets are location checks (0 to 4).
    0: Disables bonus pet checks.
    1-4: Bonus Pet 1 through the selected number are location checks."""
    display_name = "Bonus Pet Locations"
    range_start = 0
    range_end = 4
    default = 0


class UpgradeAvailability(Choice):
    """Choose when received upgrade items are available during each level
    0: Upgrades are immediately applied once received
    1: Upgrades are available for free once received
    2: Upgrades are available for normal price once received"""
    display_name = "Upgrade Availability"
    option_always = 0
    option_free = 1
    option_normal_price = 2
    default = 1

class BonusLevelTicketWeight(Range):
    """
    This is summed with other bonus item weights to determine the probability 
    of receiving extra bonus levels.
    """
    display_name = "Bonus Level Ticket Weight"
    range_start = 0
    range_end = 100
    default = 10

class BonusMoneyWeight(Range):
    """
    This is summed with other bonus item weights to determine the probability 
    of receiving bonus money.
    """
    display_name = "Bonus Money Weight"
    range_start = 1
    range_end = 100
    default = 50

class BonusStartingGuppies(Range):
    """
    Maximum number of Bonus Starting Guppies that can be included in the filler pool.
    Each filler item has a 50% chance of being a Bonus Starting Guppy until this maximum is reached.
    Remaining filler items will fall back to the other bonus item pool.
    """
    display_name = "Bonus Starting Guppies"
    range_start = 0
    range_end = 10
    default = 5


class IncludeTimeTrials(DefaultOnToggle):
    """Include 4 Time Trial completion checks in the randomizer pool.
    NOTE: This option is overwritten by 'Time Trial Required' if enabled."""
    display_name = "Include Time Trials"

class IncludeChallengeMode(DefaultOnToggle):
    """Include 4 Challenge Mode completion checks in the randomizer pool.
    NOTE: This option is overwritten by 'Challenge Mode Required' if enabled."""
    display_name = "Include Challenge Mode"

class Aliensanity(DefaultOnToggle):
    """Choose if defeating aliens for the first time is a check"""
    display_name = "Aliensanity"

class AlienRandomization(DefaultOnToggle):
    """Randomize which tanks each alien appears in.
    Each tank will contain 3-4 aliens, and each alien will appear in at least 2 tanks."""
    display_name = "Alien Randomization"

class TrapChance(Range):
    """Percentage chance to replace non-progression filler items with traps."""
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 20

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


class DeathLink(BaseDeathLink):
    """When enough of your fish die, a Death Link is sent to everyone who enabled death link.
    If another player dies, you will receive a death link penalty in your current tank."""

class DeathLinkAmnesty(Range):
    """Number of fish that must die in your tank before sending a Death Link to other players."""
    display_name = "Death Link Fish Threshold"
    range_start = 1
    range_end = 100
    default = 10

class DeathLinkEffect(Choice):
    """Choose what happens when you receive a Death Link from another player.
    Kill All Fish: Instantly kills all fish currently in your tank.
    Activate Trap: Queues a random trap."""
    display_name = "Death Link Receive Effect"
    option_kill_all_fish = 0
    option_activate_trap = 1
    default = 0


@dataclass
class InsaniquariumOptions(PerGameCommonOptions):
    starting_tank: StartingTank
    egg_pieces_per_level: EggPiecesPerLevel
    cyrax_required: CyraxRequired
    time_trial_required: TimeTrialRequired
    challenge_mode_required: ChallengeModeRequired
    upgrade_availability: UpgradeAvailability
    bonus_level_ticket_weight: BonusLevelTicketWeight
    bonus_money_weight: BonusMoneyWeight
    bonus_starting_guppies: BonusStartingGuppies
    include_time_trials: IncludeTimeTrials
    include_challenge_mode: IncludeChallengeMode
    bonus_pet_locations: BonusPetLocations
    aliensanity: Aliensanity
    alien_randomization: AlienRandomization
    trap_chance: TrapChance
    alien_attack_trap_weight: AlienAttackTrapWeight
    famine_trap_weight: FamineTrapWeight
    start_inventory_from_pool: StartInventoryPool
    starting_pet_slots: StartingPetSlots
    pet_slot_items: PetSlotItems
    death_link: DeathLink
    death_link_amnesty: DeathLinkAmnesty
    death_link_effect: DeathLinkEffect


insaniquarium_option_groups = [
    OptionGroup("Game Options", [
        StartingTank,
        UpgradeAvailability,
        StartingPetSlots,
        PetSlotItems,
    ]),
    OptionGroup("Victory Conditions", [
        CyraxRequired,
        TimeTrialRequired,
        ChallengeModeRequired,
    ]),
    OptionGroup("Included Locations", [
        EggPiecesPerLevel,
        IncludeTimeTrials,
        IncludeChallengeMode,
        BonusPetLocations,
        Aliensanity,
        AlienRandomization,
    ]),
    OptionGroup("Bonus Items", [ 
        BonusStartingGuppies,
        BonusMoneyWeight,
        BonusLevelTicketWeight,
    ]),
    OptionGroup("Traps", [
        TrapChance,
        AlienAttackTrapWeight,
        FamineTrapWeight,
    ]),
    OptionGroup("Death Link", [
        DeathLink,
        DeathLinkAmnesty,
        DeathLinkEffect,
    ], start_collapsed=True),
]
