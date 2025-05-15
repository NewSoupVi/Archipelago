from logging import debug

from BaseClasses import ItemClassification

from worlds.AutoWorld import World

EXTRA_PROGUSEFULS = {
    "Pokemon Emerald": {"HM03 Surf"},
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
