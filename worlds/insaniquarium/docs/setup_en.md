# Insaniquarium Deluxe Archipelago Setup Guide

## Required Software

- **Insaniquarium Deluxe** (Disk or Steam version)
- **Archipelago**: Version `0.6.7` or newer
- **Insaniquarium Client**: Download from [Github repository](https://github.com/benyoung32/WinFish) or provided `winfish-source` folder

## Installation

1. Download and install the provided `insaniquarium.apworld` from the file below
2. Download the modified client from the files below or from the [Github repository](https://github.com/benyoung32/WinFish)
3. Copy the data asset folders (data, properties, fishsongs...) and `bass.dll` from your copy of Insaniquarium Deluxe into the decompilation's root directory

## Generating

1. Download `Insaniquarium Deluxe.yaml`
2. Edit your desired options, save, and move the yaml file in your Players folder
3. Generate using the Archipelago Launcher interface
4. Inside the AP output file you will receive an `.apinsani` patch file containing the information needed by the client

## Playing

1. Launch **Insaniquarium Deluxe.exe** from inside the `winfish-source` after copying in the necessary asset folders
2. From the main menu, go to the profile selection screen
3. Click the **Import** button
4. Select your generated `.apinsani` patch file
5. Enter your Archipelago connection information:
   - **Server / Host**: Host address and port (e.g., `archipelago.gg:38281` or `localhost:38281`)
   - **Slot Name**: The player name specified in your configuration YAML (`name: Player1`).
   - **Password**: Password for the room (leave blank if none)