import json
import os
import tempfile
import zipfile

from worlds.Files import is_ap_player_container
from . import InsaniquariumTestBase
from ..container import InsaniquariumContainer, generate_users_dat, generate_user1_dat


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
                self.assertIn("userdata/users.dat", namelist)
                self.assertIn("userdata/user1.dat", namelist)
                self.assertIn("users.dat", namelist)
                self.assertIn("user1.dat", namelist)
                self.assertIn("slot_data.json", namelist)

                # Check manifest contents
                manifest = json.loads(zf.read("archipelago.json"))
                self.assertEqual(manifest["game"], "Insaniquarium Deluxe")
                self.assertEqual(manifest["player"], self.player)

                # Check slot data
                slot_data = json.loads(zf.read("slot_data.json"))
                self.assertIn("starting_tank_unlock", slot_data)

                # Check user1.dat length and starting tank
                user1 = zf.read("userdata/user1.dat")
                self.assertEqual(len(user1), 232)
                # Tank 2 was selected in options
                self.assertEqual(int.from_bytes(user1[0x08:0x0C], "little"), 2)

                # Check users.dat has player name
                users = zf.read("userdata/users.dat")
                player_name_bytes = self.world.player_name.encode("latin-1", errors="replace")
                self.assertIn(player_name_bytes, users)

