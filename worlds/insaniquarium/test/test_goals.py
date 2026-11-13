from . import InsaniquariumTestBase
from ..data.item_data import (
    TANK_2_UNLOCK,
    TANK_3_UNLOCK,
    TANK_4_UNLOCK,
)


class TestGoalDefeatCyrax(InsaniquariumTestBase):
    options = {
        "cyrax_required": True,
        "time_trial_required": False,
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


class TestGoalAllTanksOnly(InsaniquariumTestBase):
    options = {
        "cyrax_required": False,
        "time_trial_required": False,
        "starting_tank": 1,
    }

    def test_all_tanks_logic(self) -> None:
        self.assertBeatable(False)

        # Collect all tank unlocks -> Tanks 1-4 complete
        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK])
        self.assertBeatable(True)


class TestGoalTimeTrialsRequired(InsaniquariumTestBase):
    options = {
        "cyrax_required": False,
        "time_trial_required": True,
        "starting_tank": 1,
    }

    def test_time_trials_logic(self) -> None:
        self.assertBeatable(False)

        # Collect all tank unlocks -> Tanks 1-4 and Time Trials accessible
        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK, TANK_4_UNLOCK])
        self.assertBeatable(True)


class TestGoalCyraxAndTimeTrials(InsaniquariumTestBase):
    options = {
        "cyrax_required": True,
        "time_trial_required": True,
        "starting_tank": 1,
    }

    def test_cyrax_and_time_trials_logic(self) -> None:
        self.assertBeatable(False)

        self.collect_by_name([TANK_2_UNLOCK, TANK_3_UNLOCK])
        self.assertBeatable(False)

        self.collect_by_name(TANK_4_UNLOCK)
        self.assertBeatable(True)
