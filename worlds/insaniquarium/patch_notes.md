### Fixes

- **Pet Slot Upgrades** Pet slot upgrades should now work properly
- **Cyrax** Cyrax is now available with a new button in the tank select screen after completing all 4 tanks
- ****  

### New Checks & Logic

- **Challenge Mode Checks**: Added 4 new location checks for completing each tank's Challenge Mode (`Challenge 1 Complete` through `Challenge 4 Complete`), bringing total locations to 77
- **Alien Defeat Checks**: Added 7 new location checks for defeating each alien in the game with `aliensanity` enabled

### New YAML Options

- **`upgrade_availability`**: Control when received weapon/food/slot upgrades are available in-level (`always`, `free` upon receiving, or `normal_price`).
- **`starting_pet_slots`**: choose how many pet slots to start with
- **`pet_slot_items`**: choose how many pet slots are distributed in the item pool
- **`bonus_pet_locations`**: Control how many bonus pets are location checks (0 to 4, default 4). Setting to 0 disables bonus pet locations
- **`aliensanity`**: Option toggle prepared for future alien defeat checks
  
### Modular Victory Conditions

- Completing all 4 Adventure Tanks is now always a base victory requirement.
- **`cyrax_required`**: Choose whether defeating Cyrax in Tank 5 is required to win (default: `true`)
- **`time_trial_required`**: Choose whether all 4 Time Trials must be completed to win (default: `false`). Automatically ensures Time Trial checks are included in the pool
- **`challenge_mode_required`**: Choose whether all 4 Challenge Mode tanks must be completed to win (default: `false`)
