### Client Updates

- **Simplified Connection Process** - Removed the need to create and import a patch file per save. All option information is now handled by the connection handshake between client and server
- **Bigger windowed mode** - Added a 2x scale option to the pause menu to make the game more playable in windowed mode! Still research to be done for borderless windowed mode  
- **Archibald sprite** - The archibald sprite created by bootsowen is now displayed in game, and the hatching screen has been reworked to reflect progress in the Archipelago

### Changes

- **Priority Locations** - Added priority locations to make progression items more likely to show up in exciting places
- **Bonus Shell Tickets** - The bonus shell filler item no longer just gives shells, it now gives a ticket to start a random tank's bonus round from the tank select. Gotta earn those shells!

### New YAML Options

- **Death Link** (`death_link`) - Toggle Death Link integration. Now your friends can share in the insanity!
- **Death Link Fish Amnesty** (`death_link_amnesty`) - Configures how many fish must die before sending a Death Link.
- **Death Link Receive Effect** (`death_link_effect`) - Configures the penalty when receiving a Death Link (kill all fish or activate trap)
- **Alien Randomization** (`alien_randomization`) - Randomizes which tanks each alien appears in. Each tank has 3-4 aliens, and each alien appears in at least 2 tanks. Each level deeper in a tank has more chance to spawn two at once. Good luck with the 1-1 bilaterus ;)