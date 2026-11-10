from . import InsaniquariumTestBase


class TestEggPieces1(InsaniquariumTestBase):
    options = {
        "egg_pieces_per_level": 1,
    }

    def test_egg_pieces_1_counts_and_locations(self) -> None:
        unfilled_locs = self.multiworld.get_unfilled_locations(self.player)
        self.assertEqual(len(unfilled_locs), 37)
        self.assertEqual(len(self.multiworld.itempool), 37)

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
        self.assertEqual(len(unfilled_locs), 57)
        self.assertEqual(len(self.multiworld.itempool), 57)

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
        self.assertEqual(len(unfilled_locs), 77)
        self.assertEqual(len(self.multiworld.itempool), 77)

        loc_names = {loc.name for loc in unfilled_locs}
        self.assertIn("Tank 1-1 Egg Piece 1", loc_names)
        self.assertIn("Tank 1-1 Egg Piece 2", loc_names)
        self.assertIn("Tank 1-1 Egg Piece 3", loc_names)
        self.assertIn("Cyrax", loc_names)

