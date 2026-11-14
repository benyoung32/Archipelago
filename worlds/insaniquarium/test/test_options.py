from . import InsaniquariumTestBase
from ..data.item_data import (
    STARTING_MONEY,
    TRAP_ALIEN_ATTACK,
    TRAP_FAMINE,
)


class TestExcludeTimeTrials(InsaniquariumTestBase):
    options = {
        "include_time_trials": False,
    }

    def test_time_trials_excluded(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        loc_names = {loc.name for loc in unfilled_locs}
        self.assertNotIn("Time Trial 1 Complete", loc_names)
        self.assertNotIn("Time Trial 2 Complete", loc_names)
        self.assertNotIn("Time Trial 3 Complete", loc_names)
        self.assertNotIn("Time Trial 4 Complete", loc_names)
        self.assertEqual(len(unfilled_locs), 76)
        self.assertEqual(len(self.multiworld.itempool), 76)


class TestExcludeBonusPets(InsaniquariumTestBase):
    options = {
        "bonus_pet_locations": 0,
    }

    def test_bonus_pets_excluded(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        loc_names = {loc.name for loc in unfilled_locs}
        self.assertNotIn("Bonus Pet 1", loc_names)
        self.assertNotIn("Bonus Pet 2", loc_names)
        self.assertNotIn("Bonus Pet 3", loc_names)
        self.assertNotIn("Bonus Pet 4", loc_names)
        self.assertEqual(len(unfilled_locs), 80)
        self.assertEqual(len(self.multiworld.itempool), 80)


class TestPartialBonusPets(InsaniquariumTestBase):
    options = {
        "bonus_pet_locations": 2,
    }

    def test_partial_bonus_pets(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        loc_names = {loc.name for loc in unfilled_locs}
        self.assertIn("Bonus Pet 1", loc_names)
        self.assertIn("Bonus Pet 2", loc_names)
        self.assertNotIn("Bonus Pet 3", loc_names)
        self.assertNotIn("Bonus Pet 4", loc_names)
        self.assertEqual(len(unfilled_locs), 82)
        self.assertEqual(len(self.multiworld.itempool), 82)


class TestAliensanity(InsaniquariumTestBase):
    options = {
        "aliensanity": False,
    }

    def test_aliensanity_excluded_when_false(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        loc_names = {loc.name for loc in unfilled_locs}
        self.assertNotIn("Defeat Sylvester", loc_names)
        self.assertNotIn("Defeat Balrog", loc_names)
        self.assertNotIn("Defeat Gus", loc_names)
        self.assertNotIn("Defeat Destructor", loc_names)
        self.assertNotIn("Defeat Psychosquid", loc_names)
        self.assertNotIn("Defeat Ulysses", loc_names)
        self.assertNotIn("Defeat Bilaterus", loc_names)
        # 80 default - 7 alien checks = 73 locations
        self.assertEqual(len(unfilled_locs), 73)
        self.assertEqual(len(self.multiworld.itempool), 73)


class TestTrapChance100(InsaniquariumTestBase):
    options = {
        "trap_chance": 100,
    }

    def test_all_filler_are_traps(self) -> None:
        itempool_names = [item.name for item in self.multiworld.itempool]
        self.assertNotIn(STARTING_MONEY, itempool_names)
        trap_count = itempool_names.count(TRAP_ALIEN_ATTACK) + itempool_names.count(TRAP_FAMINE)
        self.assertGreater(trap_count, 0)
        self.assertEqual(len(self.multiworld.itempool), len(self.multiworld.get_unfilled_locations(self.player)))


class TestMinimalLocations(InsaniquariumTestBase):
    auto_construct = False
    options = {
        "egg_pieces_per_level": 1,
        "include_time_trials": False,
        "bonus_pet_locations": 0,
        "aliensanity": False,
    }

    def test_too_few_locations_raises_option_error(self) -> None:
        from Options import OptionError
        with self.assertRaises(OptionError):
            self.world_setup()

