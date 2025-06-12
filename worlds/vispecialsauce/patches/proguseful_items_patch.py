from logging import debug

from BaseClasses import ItemClassification

from worlds.AutoWorld import World

EXTRA_PROGUSEFULS = {
    "A Link to the Past": {"Moon Pearl"},
    "Clique": {"Button Activation"},
    "Factorio": {"Progressive Science Pack"},
    "Inscryption": {"Inspectometer Battery", "Pile of Meat", "Camera Replica", "Epitaph Pieces", "Film Roll"},
    "Lingo": {"Red", "Blue", "Black", "Yellow", "Crossroads - Roof Access"},
    "Minecraft": {"Progressive Armor", "Progressive Weapons", "Progressive Tools"},
    "Pokemon Emerald": {"HM03 Surf", "Balance Badge", "HM06 Rock Smash", "Dynamo Badge", "HM02 Fly"},
    "Ocarina of Time": {"Progressive Hookshot", "Progressive Bomb Bag", "Zelda's Lullaby", "Bow"},
    "Slay the Spire": {"Boss Relic"},
    "Super Mario 64": {"Progressive Key", "Basement Key", "Second Floor Key", "Side Flip", "Backflip", "Ledge Grab", "Long Jump", "Triple Jump", "Wall Kick"},
    "Super Mario World": {"Progressive Powerup", "Yoshi", "Carry", "Climb", "Run", "Swim"},
    "Timespinner": {"Celestial Sash", "Talaria Attachment", "Succubus Hairpin", "Lightwall", "Djinn Inferno", "Twin Pyramid Key", "Timeworn Warp Beacon", "Modern Warp Beacon", "Mysterious Warp Beacon"},
}


def run_proguseful_patch_single_world(game_name: str, world: type[World]) -> None:
    if game_name not in EXTRA_PROGUSEFULS:
        return

    extra_proguseful_items_for_this_world = EXTRA_PROGUSEFULS[game_name]

    original_fill_hook = world.fill_hook

    def patched_fill_hook(self, progitempool, usefulitempool, filleritempool, fill_locations):
        ret = original_fill_hook(self, progitempool, usefulitempool, filleritempool, fill_locations)

        for item in progitempool:
            if item.advancement and not item.useful and item.name in extra_proguseful_items_for_this_world:
                debug(f"Making {item.name} proguseful.")
                item.classification |= ItemClassification.useful

        return ret

    world.fill_hook = patched_fill_hook


def run_fill_patch() -> None:
    from worlds import AutoWorldRegister

    for game_name, world_type in AutoWorldRegister.world_types.items():
        run_proguseful_patch_single_world(game_name, world_type)
