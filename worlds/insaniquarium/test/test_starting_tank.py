from . import InsaniquariumTestBase
from ..item_data import (
    TANK_1_UNLOCK,
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
)


class TestStartingTank1(InsaniquariumTestBase):
    options = {
        "starting_tank": 1,
    }

    def test_starting_tank_1_unlocked(self) -> None:
        self.assertEqual(self.world.starting_tank_unlock, TANK_1_UNLOCK)
        self.assertTrue(self.can_reach_region("Tank 1"))
        self.assertFalse(self.can_reach_region("Tank 2"))
        self.assertFalse(self.can_reach_region("Tank 3"))
        self.assertFalse(self.can_reach_region("Tank 4"))

        # Test collecting Tank 2 unlock allows entry to Tank 2
        self.collect_by_name(TANK_2_UNLOCK)
        self.assertTrue(self.can_reach_region("Tank 2"))


class TestStartingTank2(InsaniquariumTestBase):
    options = {
        "starting_tank": 2,
    }

    def test_starting_tank_2_unlocked(self) -> None:
        self.assertEqual(self.world.starting_tank_unlock, TANK_2_UNLOCK)
        self.assertTrue(self.can_reach_region("Tank 2"))
        self.assertFalse(self.can_reach_region("Tank 1"))
        self.assertFalse(self.can_reach_region("Tank 3"))
        self.assertFalse(self.can_reach_region("Tank 4"))


class TestStartingTank3(InsaniquariumTestBase):
    options = {
        "starting_tank": 3,
    }

    def test_starting_tank_3_unlocked(self) -> None:
        self.assertEqual(self.world.starting_tank_unlock, TANK_3_UNLOCK)
        self.assertTrue(self.can_reach_region("Tank 3"))
        self.assertFalse(self.can_reach_region("Tank 1"))
        self.assertFalse(self.can_reach_region("Tank 2"))
        self.assertFalse(self.can_reach_region("Tank 4"))


class TestStartingTank4(InsaniquariumTestBase):
    options = {
        "starting_tank": 4,
    }

    def test_starting_tank_4_unlocked(self) -> None:
        self.assertEqual(self.world.starting_tank_unlock, TANK_4_UNLOCK)
        self.assertTrue(self.can_reach_region("Tank 4"))
        self.assertFalse(self.can_reach_region("Tank 1"))
        self.assertFalse(self.can_reach_region("Tank 2"))
        self.assertFalse(self.can_reach_region("Tank 3"))


class TestStartingTankRandom(InsaniquariumTestBase):
    options = {
        "starting_tank": "random",
    }

    def test_random_starting_tank(self) -> None:
        all_unlocks = {TANK_1_UNLOCK, TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK}
        self.assertIn(self.world.starting_tank_unlock, all_unlocks)
        # Ensure remaining 3 unlocks are in itempool
        itempool_names = [item.name for item in self.multiworld.itempool]
        remaining_unlocks = all_unlocks - {self.world.starting_tank_unlock}
        for unlock in remaining_unlocks:
            self.assertIn(unlock, itempool_names)
        self.assertNotIn(self.world.starting_tank_unlock, itempool_names)
