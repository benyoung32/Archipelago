## Required Software

- **Insaniquarium Deluxe** (Disk or Steam version)
- **Archipelago**: Version `0.6.7` or newer
- **Insaniquarium Client**: Download from [Github repository](https://github.com/benyoung32/WinFish) or provided `winfish-source` folder. This is a modified version of the WinFish decompilation project. It only includes the code, assets from your copy of the game are needed to run it

## Installation

1. Download the provided `insaniquarium.apworld` from the file below and install into the Archipelago Launcher
2. Download the modified client from the files below or from the [Github repository](https://github.com/benyoung32/WinFish)
3. Copy the data asset folders (data, properties, fishsongs...) and `bass.dll` from your copy of Insaniquarium Deluxe into the clients's root directory

## Generating

1. Download `Insaniquarium Deluxe.yaml`
2. Edit your desired options, save, and move the yaml file in your Players folder
3. Generate APWorld using the Archipelago Launcher

## Playing

1. Launch **Insaniquarium Deluxe.exe** from inside the `winfish-source` zip after copying in the necessary asset folders
2. From the main menu, go to the profile selection screen
3. Click the `NEW CONNECTION` button
4. Enter your Archipelago connection information:
   - **Server / Host**: Host address and port (e.g., `archipelago.gg:38281` or `localhost:38281`)
   - **Slot Name**: The player name specified in your configuration YAML (`name: Player1`).
   - **Password**: Password for the room (leave blank if none)