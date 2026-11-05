from . import InsaniquariumTestBase


class TestEggPieces1(InsaniquariumTestBase):
    options = {
        "egg_pieces_per_level": 1,
    }

    def test_egg_pieces_1_counts_and_locations(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        self.assertEqual(len(unfilled_locs), 33)
        self.assertEqual(len(self.multiworld.itempool), 33)

        loc_names = {loc.name for loc in unfilled_locs}
        self.assertIn("Tank 1-1 Egg Piece 3", loc_names)
        self.assertNotIn("Tank 1-1 Egg Piece 1", loc_names)
        self.assertNotIn("Tank 1-1 Egg Piece 2", loc_names)


class TestEggPieces2(InsaniquariumTestBase):
    options = {
        "egg_pieces_per_level": 2,
    }

    def test_egg_pieces_2_counts_and_locations(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        self.assertEqual(len(unfilled_locs), 53)
        self.assertEqual(len(self.multiworld.itempool), 53)

        loc_names = {loc.name for loc in unfilled_locs}
        self.assertIn("Tank 1-1 Egg Piece 1", loc_names)
        self.assertNotIn("Tank 1-1 Egg Piece 2", loc_names)
        self.assertIn("Tank 1-1 Egg Piece 3", loc_names)


class TestEggPieces3(InsaniquariumTestBase):
    options = {
        "egg_pieces_per_level": 3,
    }

    def test_egg_pieces_3_counts_and_locations(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        self.assertEqual(len(unfilled_locs), 73)
        self.assertEqual(len(self.multiworld.itempool), 73)

        loc_names = {loc.name for loc in unfilled_locs}
        self.assertIn("Tank 1-1 Egg Piece 1", loc_names)
        self.assertIn("Tank 1-1 Egg Piece 2", loc_names)
        self.assertIn("Tank 1-1 Egg Piece 3", loc_names)
        self.assertIn("Cyrax", loc_names)

