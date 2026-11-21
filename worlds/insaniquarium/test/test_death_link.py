from . import InsaniquariumTestBase
from ..options import DeathLinkEffect


class TestDeathLinkDefault(InsaniquariumTestBase):
    def test_death_link_defaults(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertIn("death_link", slot_data)
        self.assertFalse(slot_data["death_link"])
        self.assertIn("death_link_amnesty", slot_data)
        self.assertEqual(slot_data["death_link_amnesty"], 10)
        self.assertIn("death_link_effect", slot_data)
        self.assertEqual(slot_data["death_link_effect"], DeathLinkEffect.option_kill_all_fish)


class TestDeathLinkCustom(InsaniquariumTestBase):
    options = {
        "death_link": True,
        "death_link_amnesty": 12,
        "death_link_effect": "activate_trap",
    }

    def test_death_link_custom_values(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertTrue(slot_data["death_link"])
        self.assertEqual(slot_data["death_link_amnesty"], 12)
        self.assertEqual(slot_data["death_link_effect"], DeathLinkEffect.option_activate_trap)

