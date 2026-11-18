from collections import Counter

from . import InsaniquariumTestBase


EXPECTED_ALIEN_LOCATIONS = [
    "Defeat Sylvester",
    "Defeat Balrog",
    "Defeat Gus",
    "Defeat Destructor",
    "Defeat Psychosquid",
    "Defeat Ulysses",
    "Defeat Bilaterus",
]

DEFAULT_ALIEN_REGIONS = {
    "Defeat Sylvester": "Tank 1",
    "Defeat Balrog": "Tank 1",
    "Defeat Gus": "Tank 2",
    "Defeat Destructor": "Tank 2",
    "Defeat Psychosquid": "Tank 3",
    "Defeat Ulysses": "Tank 3",
    "Defeat Bilaterus": "Tank 4",
}

VALID_TANKS = {"Tank 1", "Tank 2", "Tank 3", "Tank 4"}


class TestAlienRandomizationDefault(InsaniquariumTestBase):
    def test_default_alien_randomization_enabled(self) -> None:
        self.assertTrue(bool(self.world.options.alien_randomization.value))
        slot_data = self.world.fill_slot_data()
        self.assertIn("alien_randomization", slot_data)
        tank_to_aliens = slot_data["alien_randomization"]

        # Ensure all 4 adventure tanks are mapped
        self.assertEqual(set(tank_to_aliens.keys()), VALID_TANKS)

        alien_appearances = Counter()
        for tank, aliens in tank_to_aliens.items():
            # Constraint: Each tank should have 3-4 aliens in it
            self.assertGreaterEqual(len(aliens), 3, f"{tank} has fewer than 3 aliens: {aliens}")
            self.assertLessEqual(len(aliens), 4, f"{tank} has more than 4 aliens: {aliens}")

            # No duplicates in the same tank
            self.assertEqual(len(set(aliens)), len(aliens), f"{tank} has duplicate aliens: {aliens}")

            # All aliens must be valid defeat alien check names
            for alien in aliens:
                self.assertIn(alien, EXPECTED_ALIEN_LOCATIONS)
                alien_appearances[alien] += 1

        # Constraint: Each alien should appear in at least 2 tanks
        for alien in EXPECTED_ALIEN_LOCATIONS:
            count = alien_appearances[alien]
            self.assertGreaterEqual(count, 2, f"{alien} appears in {count} tanks (< 2)")

        # Verify that each alien check has a dedicated sub-region connected to all tanks where it appears
        for alien in EXPECTED_ALIEN_LOCATIONS:
            tanks_with_alien = [tank for tank in sorted(VALID_TANKS) if alien in tank_to_aliens[tank]]
            loc = self.world.get_location(alien)
            self.assertEqual(loc.parent_region.name, f"{alien} Region")
            connecting_tanks = [entrance.parent_region.name for entrance in loc.parent_region.entrances]
            self.assertEqual(sorted(connecting_tanks), sorted(tanks_with_alien))


class TestAlienRandomizationDisabled(InsaniquariumTestBase):
    options = {
        "alien_randomization": False,
    }

    def test_alien_randomization_disabled(self) -> None:
        self.assertFalse(bool(self.world.options.alien_randomization.value))
        slot_data = self.world.fill_slot_data()
        self.assertIn("alien_randomization", slot_data)
        self.assertEqual(slot_data["alien_randomization"], {})

        for loc_name, expected_tank in DEFAULT_ALIEN_REGIONS.items():
            loc = self.world.get_location(loc_name)
            self.assertEqual(loc.parent_region.name, expected_tank)


class TestAlienRandomizationWithoutAliensanity(InsaniquariumTestBase):
    options = {
        "alien_randomization": True,
        "aliensanity": False,
    }

    def test_alien_randomization_slot_data_without_checks(self) -> None:
        slot_data = self.world.fill_slot_data()
        tank_to_aliens = slot_data["alien_randomization"]

        # Slot data still provides the wave pools for all 4 tanks
        self.assertEqual(set(tank_to_aliens.keys()), VALID_TANKS)
        alien_appearances = Counter()
        for tank, aliens in tank_to_aliens.items():
            self.assertGreaterEqual(len(aliens), 3)
            self.assertLessEqual(len(aliens), 4)
            for alien in aliens:
                alien_appearances[alien] += 1

        for alien in EXPECTED_ALIEN_LOCATIONS:
            self.assertGreaterEqual(alien_appearances[alien], 2)

        # Location checks should not be present in the world when aliensanity is False
        unfilled_locs = {loc.name for loc in self.multiworld.get_unfilled_locations(self.player)}
        for loc_name in EXPECTED_ALIEN_LOCATIONS:
            self.assertNotIn(loc_name, unfilled_locs)
