from __future__ import annotations

import json
import os
import zipfile
from typing import TYPE_CHECKING, Any

from worlds.Files import APPlayerContainer

if TYPE_CHECKING:
    from . import InsaniquariumWorld

class InsaniquariumContainer(APPlayerContainer):
    """
    Container packaging slot data and metadata into an AP container file (.apinsani).
    Visible on the WebHost room page with a 'Download Patch File...' link.
    """
    game = "Insaniquarium Deluxe"
    patch_file_ending = ".apinsani"

    def __init__(
        self,
        output_directory: str,
        player: int,
        player_name: str,
        world: InsaniquariumWorld,
        server: str = ""
    ):
        self.slot_data: dict[str, Any] = world.fill_slot_data()
        base_name = world.multiworld.get_out_file_name_base(player)

        container_path = os.path.join(output_directory, f"{base_name}{self.patch_file_ending}")
        super().__init__(container_path, player, player_name, server)

    def write_contents(self, opened_zipfile: zipfile.ZipFile) -> None:
        # Write slot_data.json
        opened_zipfile.writestr("slot_data.json", json.dumps(self.slot_data, indent=2))

        # Writes archipelago.json manifest (enabling WebHost detection and download link)
        super().write_contents(opened_zipfile)

