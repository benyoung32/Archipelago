### Client Updates

- **Archibald sprite** - The archibald sprite created by discord @bootsowen is now displayed in game, and the hatching screen has been reworked to reflect progress in the Archipelago
- **Simplified Connection Process** - Removed the need to create and import a patch file per save. All option information is now handled by the connection handshake between client and server
- **Bigger windowed mode** - Added a 2x scale option to the pause menu to make the game more playable in windowed mode! Still research to be done for borderless windowed mode  
- **Autofire Setting** - Wrist getting tired? New check box added to the pause menu to enable the rapid fire weapon mode which is typically locked to the max weapon upgrade

### Changes

- **Priority Locations** - Tank completions are now marked as priority to make progression items more likely to show up in exciting places. Aliens are also priority if aliensanity is enabled.
- **Bonus Shell Tickets** - The bonus shell filler item no longer just gives shells, it now gives a ticket to start a random tank's bonus round from the tank select. Gotta earn those shells!
- **Bonus Pet Locations** (`bonus_pet_locations`) - Bonus pets are now always included as locations. This option now chooses how many bonus pet locations are allowed as default locations (can hold progression) vs filler only (0-4).

### New YAML Options

- **Death Link** (`death_link`) - Toggle Death Link integration. Now your friends can share in the insanity!
- **Death Link Fish Amnesty** (`death_link_amnesty`) - Configures how many fish must die before sending a Death Link
- **Death Link Receive Effect** (`death_link_effect`) - Configures the penalty when receiving a Death Link (kill all fish or activate trap)
- **Alien Randomization** (`alien_randomization`) - Randomizes which tanks each alien appears in. Each tank has 3-4 aliens, and each alien appears in at least 2 tanks. Each level deeper in a tank has more chance to spawn two at once. Good luck with the 1-1 bilaterus ;)
- **Bonus Starting Guppies** (`bonus_starting_guppies`) - Sets the maximum number of bonus starting guppies included in the filler pool (0-10). Each filler item has a 50% chance of being a bonus starting guppy until this limit is reached

### Planned Features

- **Info Page** - New GUI page added to the client to track remaining checks, received items, and goal progress
- **Tracker integration** - Integrate APWorld with pop tracker