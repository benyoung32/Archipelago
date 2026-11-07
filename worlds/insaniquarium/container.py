from __future__ import annotations

import json
import os
import struct
import zipfile
from typing import Optional, TYPE_CHECKING, Any

from worlds.Files import APPlayerContainer

if TYPE_CHECKING:
    from . import InsaniquariumWorld

# Base 232-byte template for user1.dat save file
DEFAULT_USER1_BYTES = bytes([
    0x00, 0x00, 0x00, 0x80, 0x43, 0x2F, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2D, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x82, 0x00, 0x00, 0x00,
    0x8E, 0x00, 0x00, 0x00, 0xA6, 0x00, 0x00, 0x00, 0xF1, 0x00, 0x00, 0x00, 0x2B, 0x01, 0x00, 0x00,
    0x27, 0x01, 0x00, 0x00, 0xE7, 0x00, 0x00, 0x00, 0xB7, 0x01, 0x00, 0x00, 0x15, 0x02, 0x00, 0x00,
    0xE2, 0x01, 0x00, 0x00, 0xDA, 0x01, 0x00, 0x00, 0x09, 0x01, 0x00, 0x00, 0x96, 0x01, 0x00, 0x00,
    0x08, 0x02, 0x00, 0x00, 0xA3, 0x01, 0x00, 0x00, 0xB5, 0x01, 0x00, 0x00, 0x53, 0x01, 0x00, 0x00,
    0x46, 0x02, 0x00, 0x00, 0x5B, 0x03, 0x00, 0x00, 0x97, 0x02, 0x00, 0x00, 0x41, 0x03, 0x00, 0x00,
    0x04, 0x00, 0x00, 0x00, 0xA6, 0x74, 0xBD, 0x62
])


def generate_users_dat(player_name: str) -> bytes:
    """
    Generate PopCap SexyAppFramework users.dat binary registry for a single player profile.
    """
    clean_name = player_name[:16].encode("latin-1", errors="replace")
    payload = bytearray()
    payload.extend(struct.pack("<H", 1))                # num_users = 1
    payload.extend(struct.pack("<H", len(clean_name)))  # string length
    payload.extend(clean_name)                          # profile name
    payload.extend(struct.pack("<II", 1, 1))            # user_id = 1, use_seq = 1
    header = struct.pack("<I", len(payload))
    return bytes(header + payload)


def generate_user1_dat(world: Optional[InsaniquariumWorld] = None) -> bytes:
    """
    Generate initial user1.dat progression save file configured for the world seed options.
    """
    data = bytearray(DEFAULT_USER1_BYTES)

    if world is not None:
        tank_num = 1
        unlock_name = getattr(world, "starting_tank_unlock", "")
        if "Tank 2" in unlock_name:
            tank_num = 2
        elif "Tank 3" in unlock_name:
            tank_num = 3
        elif "Tank 4" in unlock_name:
            tank_num = 4

        # Set initial tank and level numbers
        struct.pack_into("<I", data, 0x08, tank_num)
        struct.pack_into("<I", data, 0x0C, 1)  # level 1
        struct.pack_into("<I", data, 0x10, tank_num)

    return bytes(data)


class InsaniquariumContainer(APPlayerContainer):
    """
    Container packaging player userdata save files into an AP container file.
    Visible on the WebHost room page with a 'Download Patch File...' link.
    """
    game = "Insaniquarium Deluxe"
    patch_file_ending = ".apinsani"

    def __init__(
        self,
        output_directory: str,
        player: int,
        player_name: str,
        world: Optional[InsaniquariumWorld] = None,
        user1_data: Optional[bytes] = None,
        users_data: Optional[bytes] = None,
        server: str = "",
    ):
        self.user1_data = user1_data or generate_user1_dat(world)
        self.users_data = users_data or generate_users_dat(player_name)
        self.slot_data: Optional[dict[str, Any]] = world.fill_slot_data() if world else None

        if world and hasattr(world, "multiworld"):
            base_name = world.multiworld.get_out_file_name_base(player)
        else:
            base_name = f"AP_{player}_{player_name}"

        container_path = os.path.join(output_directory, f"{base_name}{self.patch_file_ending}")
        super().__init__(container_path, player, player_name, server)

    def write_contents(self, opened_zipfile: zipfile.ZipFile) -> None:
        # Write userdata files in userdata/ directory (matching standard installation structure)
        opened_zipfile.writestr("users.dat", self.users_data)
        opened_zipfile.writestr("user1.dat", self.user1_data)

        # Write slot_data.json if available
        if self.slot_data is not None:
            opened_zipfile.writestr("slot_data.json", json.dumps(self.slot_data, indent=2))

        # Writes archipelago.json manifest (enabling WebHost detection and download link)
        super().write_contents(opened_zipfile)

