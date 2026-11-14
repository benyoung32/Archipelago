# Insaniquarium Deluxe Archipelago Setup Guide

## Required Software

- **Insaniquarium Deluxe** (PC version).
- **Archipelago**: Version `0.6.7` or newer.
- [**Insaniquarium Deluxe Archipelago Client**](https://github.com/benyoung32/WinFish)

## Installation

1. Download the modified [Insaniquarium Deluxe Decompilation](https://github.com/benyoung32/WinFish) forked from the WinFish project.
2. Copy the asset folders (data, properties, fishsongs...) and `bass.dll` from your copy of Insaniquarium Deluxe to the decompilation's root directory.

## Generating a Multiworld Game

1. Obtain a player configuration file (`Insaniquarium.yaml`):
   - You can configure and export your YAML using the [Insaniquarium Deluxe WebHost Options Page](../player-options).
   - Alternatively, generate template YAMLs through the Archipelago Launcher (**Generate Template Options**) or use `Players/Templates/Insaniquarium Deluxe.yaml`.
2. When the generation completes, you will receive an `.apinsani` patch file.

## Connecting and Playing

1. Launch **Insaniquarium Deluxe**.
2. From the main menu, go to the profile selection screen.
3. Click the **Import** button.
4. Select your generated `.apinsani` patch file.
5. Enter your Archipelago connection information:
   - **Server / Host**: Host address and port (e.g., `archipelago.gg:38281` or `localhost:38281`).
   - **Slot Name**: The player name specified in your configuration YAML (`name: Player1`).
   - **Password**: Password for the room (leave blank if none).