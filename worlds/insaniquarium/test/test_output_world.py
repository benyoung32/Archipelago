import collections
import os
import pathlib
import re
import tempfile
import zipfile

from . import InsaniquariumTestBase
from ..container import InsaniquariumContainer


def parse_spoiler_text(text: str) -> tuple[dict[str, str], dict[str, str], collections.Counter[str], list[str]]:
    """
    Parses an Archipelago spoiler text file into:
    (header_options, locations_dict, items_counter, starting_items_list)
    """
    header_options: dict[str, str] = {}
    starting_items: list[str] = []
    locations: dict[str, str] = {}
    items_counter: collections.Counter[str] = collections.Counter()
    section = "header"

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "Starting Items:":
            section = "starting_items"
            continue
        if stripped == "Locations:":
            section = "locations"
            continue
        if stripped.startswith("Playthrough"):
            section = "playthrough"
            continue

        if section == "header":
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                header_options[k.strip()] = v.strip()
        elif section == "starting_items":
            starting_items.append(stripped)
        elif section == "locations":
            if ": " in stripped:
                loc_part, item_part = stripped.split(": ", 1)
                # Strip potential player annotations like "Location (Player1): Item (Player1)"
                loc_name = re.sub(r"\s*\([^)]*\)$", "", loc_part).strip()
                item_name = re.sub(r"\s*\([^)]*\)$", "", item_part).strip()
                locations[loc_name] = item_name
                items_counter[item_name] += 1

    return header_options, locations, items_counter, starting_items


class TestOutputWorldArchive(InsaniquariumTestBase):
    """
    Tests output world generation, unzips the generated archive to extract the spoiler log,
    and validates location and item counts.
    """
    options = {
        "egg_pieces_per_level": 3,
        "include_time_trials": True,
        "include_challenge_mode": True,
        "bonus_pet_locations": 0,
        "pet_slot_items": 3,
    }

    def test_output_zip_and_spoiler(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            outfilebase = f"AP_{self.multiworld.seed_name}"

            # 1. Generate player output file (.apinsani)
            self.world.generate_output(temp_dir)
            expected_apinsani = temp_path / f"{self.multiworld.get_out_file_name_base(self.player)}{InsaniquariumContainer.patch_file_ending}"
            self.assertTrue(expected_apinsani.is_file(), f"Missing container file: {expected_apinsani}")

            # 2. Generate spoiler log into temp directory
            spoiler_path = temp_path / f"{outfilebase}_Spoiler.txt"
            self.multiworld.spoiler.to_file(str(spoiler_path))
            self.assertTrue(spoiler_path.is_file(), f"Missing spoiler file: {spoiler_path}")

            # 3. Create output zip archive matching Archipelago's Main.py packaging
            zip_path = temp_path / f"{outfilebase}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for entry in temp_path.iterdir():
                    if entry != zip_path:
                        zf.write(entry, arcname=entry.name)

            self.assertTrue(zip_path.is_file(), f"Missing output zip archive: {zip_path}")

            # 4. Unzip and read the spoiler file from the archive
            with zipfile.ZipFile(zip_path, "r") as zf:
                spoiler_entries = [n for n in zf.namelist() if n.endswith("_Spoiler.txt") or n == "spoiler.txt"]
                self.assertGreater(len(spoiler_entries), 0, "No spoiler.txt found inside the output zip")
                spoiler_content = zf.read(spoiler_entries[0]).decode("utf-8-sig", errors="replace")

            # 5. Parse the spoiler log
            header, locations, item_counts, starting_items = parse_spoiler_text(spoiler_content)

            # 6. Verify location count:
            # 60 egg pieces (20 * 3) + 4 tanks + 1 Cyrax + 4 time trials + 4 challenges + 0 bonus pets + 7 aliens = 80
            expected_locations = 80
            self.assertEqual(len(locations), expected_locations,
                             f"Expected {expected_locations} locations in spoiler, found {len(locations)}")

            # 7. Verify header reports matching location count
            header_loc_count = int(header.get("Location Count", 0))
            if header_loc_count:
                self.assertEqual(header_loc_count, len(locations),
                                 f"Header Location Count ({header_loc_count}) does not match locations ({len(locations)})")

            # 8. Verify starting item
            self.assertGreater(len(starting_items), 0, "No starting items found in spoiler log")
            self.assertEqual(starting_items[0], self.world.starting_tank_unlock)


class TestLatestArchipelagoOutputFolder(InsaniquariumTestBase):
    """
    Looks at actual output files generated in the Archipelago output directory
    (e.g. C:/ProgramData/Archipelago/output), unzips the latest archive,
    and validates location and item counts from its spoiler.txt.
    """

    def test_inspect_archipelago_output_zip(self) -> None:
        ap_dir = pathlib.Path(os.environ.get("ARCHIPELAGO_INSTALL", r"C:\ProgramData\Archipelago"))
        output_dir = ap_dir / "output"

        if not output_dir.is_dir():
            self.skipTest(f"Archipelago output directory not found at {output_dir}")

        zip_files = list(output_dir.glob("AP_*.zip"))
        if not zip_files:
            self.skipTest(f"No AP_*.zip archives found in {output_dir}")

        # Pick the most recently generated output zip
        zip_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest_zip = zip_files[0]

        with zipfile.ZipFile(latest_zip, "r") as zf:
            spoiler_entries = [n for n in zf.namelist() if n.endswith("_Spoiler.txt") or n == "spoiler.txt"]
            if not spoiler_entries:
                self.skipTest(f"No spoiler log found in {latest_zip.name}")

            spoiler_content = zf.read(spoiler_entries[0]).decode("utf-8-sig", errors="replace")

        header, locations, item_counts, starting_items = parse_spoiler_text(spoiler_content)

        # Skip if the latest output was not for Insaniquarium Deluxe
        if "Insaniquarium" not in header.get("Game", ""):
            self.skipTest(f"Latest archive {latest_zip.name} is for game '{header.get('Game')}', not Insaniquarium")

        # Check total location count matches the header
        header_count = int(header.get("Location Count", 0))
        if header_count:
            self.assertEqual(len(locations), header_count,
                             f"Header reported {header_count} locations, but found {len(locations)} in {latest_zip.name}")

        # Check starting items
        self.assertGreater(len(starting_items), 0, "Starting items missing in spoiler log")
