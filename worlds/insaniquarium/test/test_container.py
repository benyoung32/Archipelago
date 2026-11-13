import json
import os
import tempfile
import zipfile
from unittest.mock import MagicMock

from worlds.Files import is_ap_player_container
from . import InsaniquariumTestBase
from ..container import InsaniquariumContainer


class TestInsaniquariumContainer(InsaniquariumTestBase):
    options = {
        "starting_tank": 2,
    }

    def test_container_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.world.generate_output(temp_dir)

            expected_filename = (
                f"{self.multiworld.get_out_file_name_base(self.player)}"
                f"{InsaniquariumContainer.patch_file_ending}"
            )
            container_path = os.path.join(temp_dir, expected_filename)
            self.assertTrue(os.path.isfile(container_path), f"Expected container at {container_path}")

            with open(container_path, "rb") as f:
                raw_bytes = f.read()

            # Verify WebHost recognizes the file for the player slot
            self.assertTrue(
                is_ap_player_container("Insaniquarium Deluxe", raw_bytes, self.player),
                "Container was not recognized by is_ap_player_container",
            )

            with zipfile.ZipFile(container_path, "r") as zf:
                namelist = zf.namelist()
                self.assertIn("archipelago.json", namelist)
                self.assertIn("slot_data.json", namelist)

                # Check manifest contents
                manifest = json.loads(zf.read("archipelago.json"))
                self.assertEqual(manifest["game"], "Insaniquarium Deluxe")
                self.assertEqual(manifest["player"], self.player)

                # Check slot data
                slot_data = json.loads(zf.read("slot_data.json"))
                self.assertIn("starting_tank_unlock", slot_data)
                self.assertEqual(slot_data["starting_tank_unlock"], "Tank 2")

    def test_container_with_mock_world(self) -> None:
        """Verify InsaniquariumContainer works when given a mock world with multiworld attributes."""
        mock_world = MagicMock()
        mock_world.multiworld.get_out_file_name_base.return_value = "AP_MockSeed_P1_Player1"
        mock_world.fill_slot_data.return_value = {"test_slot_key": "test_slot_value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            container = InsaniquariumContainer(
                output_directory=temp_dir,
                player=1,
                player_name="Player1",
                world=mock_world,
            )
            container.write()

            expected_filename = f"AP_MockSeed_P1_Player1{InsaniquariumContainer.patch_file_ending}"
            container_path = os.path.join(temp_dir, expected_filename)
            self.assertTrue(os.path.isfile(container_path))

            with zipfile.ZipFile(container_path, "r") as zf:
                self.assertIn("archipelago.json", zf.namelist())
                self.assertIn("slot_data.json", zf.namelist())
                slot_data = json.loads(zf.read("slot_data.json"))
                self.assertEqual(slot_data["test_slot_key"], "test_slot_value")

