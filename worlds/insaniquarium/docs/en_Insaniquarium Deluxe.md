# Insaniquarium Deluxe

## What does randomization do to this game?

In Insaniquarium Deluxe, all major progression elements, pets, and upgrades are randomized into the Archipelago multiworld item pool:

- **Tank Unlocks**: You begin the game with a single unlocked tank (either randomized or selected via YAML) and must find unlocks for the remaining tanks in the multiworld.
- **Pets**: The 24 unique pets (such as Stinky the Snail, Itchy the Swordfish, Presto the Tadpole, and others) are shuffled into the item pool. Collecting pets allows you to equip them to help manage your tanks.
- **Pet Slots**: Up to 24 pet slots can be configured between starting pet slots and unlockable slot upgrade items, allowing you to bring more pets into levels simultaneously.
- **Upgrades**: Weapon level upgrades, food quality upgrades, and maximum food capacity upgrades can be found in the multiworld. Depending on the `upgrade_availability` option, received upgrades are either applied immediately, offered for free in the in-game shop, or made available for purchase at their regular coin cost.
- **Victory Items**: Progress through each tank and defeat bosses to complete your goal!

## What is a check in this game?

Locations where you receive items include:

- **Egg Purchases**: In each level purchasing egg pieces awards an Archipelago check. You can configure whether checks are awarded for only the final egg piece (20 checks), two pieces (40 checks), or all 3 egg pieces per level (60 checks).
- **Tank Clears**: Defeating each tank's final boss or completing its last level awards a completion check (`Tank 1 Complete` through `Tank 4 Complete`).
- **Bonus Pets**: Purchasing the 4 bonus pets (`Bonus Pet 1` through `Bonus Pet 4`) can optionally be included as check locations.
- **Time Trials**: Optionally include 4 completion checks for beating each tank's Time Trial mode.
- **Challenge Mode**: Optionally include 4 completion checks for beating each tank's Challenge Mode.
- **Aliensanity**: Defeating each unique alien boss/type for the first time awards an item check.

## What is the goal of Insaniquarium Deluxe when randomized?

The base requirement is always to complete all 4 Adventure Tanks. You can further customize your victory conditions in your YAML options:

- **Cyrax Required**: Choose whether you must defeat the final boss Cyrax in Tank 5.
- **Time Trial Required**: Require completing all 4 Time Trials to win.
- **Challenge Mode Required**: Require completing all 4 Challenge Mode tanks to win.

## What traps can be sent to Insaniquarium Deluxe?

If trap chance is enabled in your options, non-progression filler items may be replaced with:

- **Alien Attack Trap**: Immediately spawns an alien attack in your current tank, forcing you to defend your fish!
- **Famine Trap**: Instantly drops all fish in your tank into starvation, requiring immediate feeding to prevent losses.
