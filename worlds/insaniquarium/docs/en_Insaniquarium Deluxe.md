# Insaniquarium Deluxe

## What does randomization do to this game?

Tank order, pets, and upgrades are randomized into the Archipelago multiworld item pool:

- **Tank Unlocks**: You begin the game with a single unlocked tank and must find unlocks for the remaining tanks in the multiworld.
- **Pets**: The 24 unique pets are shuffled into the item pool.
- **Pet Slots**: How many pet slots you start with and how many pet slots are distributed as items in the multiworld is fully configurable.  
- **Upgrades**: Weapon level upgrades, food quality upgrades, and maximum food capacity upgrades can be found in the multiworld.

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

- **Cyrax Required**: Choose whether you must defeat the final boss Cyrax.
- **Time Trial Required**: Require completing all 4 Time Trials to win.
- **Challenge Mode Required**: Require completing all 4 Challenge Mode tanks to win.

## What traps can be sent to Insaniquarium Deluxe?

If trap chance is enabled in your options, non-progression filler items may be replaced with:

- **Alien Attack Trap**: Immediately spawns an alien attack in your current tank.
- **Famine Trap**: Instantly drops all fish in your tank into starvation.

## Death Link

- **Death Link** (`death_link`): Enable or disable Death Link.
- **Death Link Fish Threshold** (`death_link_amnesty`): Configure how many fish must die in your tank before triggering an outgoing Death Link to the multiworld (default: 5).
- **Death Link Receive Effect** (`death_link_effect`): Choose how your tank responds when receiving an incoming Death Link:
  - **Kill All Fish**: Instantly wipes all fish currently in your tank.
  - **Activate Trap**: Triggers a random active trap (Alien Attack or Famine Trap).
