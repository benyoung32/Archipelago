from . import InsaniquariumTestBase
from ..item_data import (
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
)


class TestGoalDefeatCyrax(InsaniquariumTestBase):
    options = {
        "goal": 0,  # Defeat Cyrax
        "starting_tank": 1,
    }

    def test_defeat_cyrax_logic(self) -> None:
        self.assertBeatable(False)

        # Collect Tank 2 and 3 unlocks (Tank 4 still missing)
        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK])
        self.assertBeatable(False)

        # Collect final tank unlock -> All 4 tanks complete -> Tank 5 accessible -> Cyrax accessible
        self.collect_by_name(TANK_4_UNLOCK)
        self.assertBeatable(True)


class TestGoalAllTanks(InsaniquariumTestBase):
    options = {
        "goal": 1,  # All Tanks
        "starting_tank": 1,
    }

    def test_all_tanks_logic(self) -> None:
        self.assertBeatable(False)

        # Collect all tank unlocks
        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK])
        self.assertBeatable(True)


class TestGoalAllTanksAndBonus(InsaniquariumTestBase):
    options = {
        "goal": 2,  # All Tanks & Bonus Pets
        "starting_tank": 1,
    }

    def test_all_tanks_and_bonus_logic(self) -> None:
        self.assertBeatable(False)

        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK])
        self.assertBeatable(True)


class TestGoalFullCompletion(InsaniquariumTestBase):
    options = {
        "goal": 3,  # Full Completion (Cyrax + Bonus Pets)
        "starting_tank": 1,
    }

    def test_full_completion_logic(self) -> None:
        self.assertBeatable(False)

        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK])
        self.assertBeatable(True)

