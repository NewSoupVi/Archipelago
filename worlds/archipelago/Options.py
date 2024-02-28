from typing import Dict, Union, List
from BaseClasses import MultiWorld
from Options import Toggle


class VersionMode(Toggle):
    "Randomly nerfs and buffs some orbs and their associated spells as well as some associated rings."
    display_name = "Version Mode"


# Some options that are available in the timespinner randomizer arent currently implemented
ArchipelagoVersionOptions = {
    "VersionMode": VersionMode
}


def is_option_enabled(world: MultiWorld, player: int, name: str) -> bool:
    return get_option_value(world, player, name) > 0


def get_option_value(world: MultiWorld, player: int, name: str) -> Union[int, Dict, List]:
    option = getattr(world, name, None)
    if option == None:
        return 0

    return option[player].value
