import typing
from logging import debug

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld

from worlds.AutoWorld import World

EXTRA_DEPRIORITIZED = {
    "Super Mario 64": {"Power Star"},
    "Ocarina of Time": {"Gold Skulltula Token"},
    "Sonic Adventure 2 Battle": {"Emblem"},
    "Hollow Knight": {"Grub", "Rancid Egg"},
}


def run_deprioritized_patch_single_world(game_name: str, world: type[World]) -> None:
    if game_name not in EXTRA_DEPRIORITIZED:
        return

    extra_deprioritized_items_for_this_world = EXTRA_DEPRIORITIZED[game_name]

    original_fill_hook = world.fill_hook

    def patched_fill_hook(self, progitempool, usefulitempool, filleritempool, fill_locations):
        ret = original_fill_hook(self, progitempool, usefulitempool, filleritempool, fill_locations)

        for item in progitempool:
            if (
                item.advancement
                and not ItemClassification.deprioritized & item.classification
                and item.name in extra_deprioritized_items_for_this_world
            ):
                debug(f"Making {item.name} deprioritized.")
                item.classification |= ItemClassification.deprioritized

        return ret

    world.fill_hook = patched_fill_hook


def run_fill_patch() -> None:
    from worlds import AutoWorldRegister

    for game_name, world_type in AutoWorldRegister.world_types.items():
        run_deprioritized_patch_single_world(game_name, world_type)


def new_priority_fill(multiworld, prioritylocations, progitempool, single_player, mark_for_locking):
    from Fill import fill_restrictive, sweep_from_pool

    regular_progression = []
    deprioritized_progression = []
    for item in progitempool:
        if ItemClassification.deprioritized & item.classification:
            deprioritized_progression.append(item)
        else:
            regular_progression.append(item)

    # "priority fill"
    # try without deprioritized items in the mix at all. This means they need to be collected into state first.
    priority_fill_state = sweep_from_pool(multiworld.state, deprioritized_progression)
    fill_restrictive(
        multiworld,
        priority_fill_state,
        prioritylocations,
        regular_progression,
        single_player_placement=single_player,
        swap=False,
        on_place=mark_for_locking,
        name="Priority Original",
        one_item_per_player=True,
        allow_partial=True,
    )

    if prioritylocations and regular_progression:
        # retry with one_item_per_player off because some priority fills can fail to fill with that optimization
        # deprioritized items are still not in the mix, so they need to be collected into state first.
        priority_retry_state = sweep_from_pool(multiworld.state, deprioritized_progression)
        fill_restrictive(
            multiworld,
            priority_retry_state,
            prioritylocations,
            regular_progression,
            single_player_placement=single_player,
            swap=False,
            on_place=mark_for_locking,
            name="Priority Retry",
            one_item_per_player=False,
            allow_partial=True,
        )

    if prioritylocations and deprioritized_progression:
        # There are no more regular progression items that can be placed on any priority locations.
        # We'd still prefer to place deprioritized progression items on priority locations over filler items.
        # Since we're leaving out the remaining regular progression now, we need to collect it into state first.
        priority_retry_2_state = sweep_from_pool(multiworld.state, regular_progression)
        fill_restrictive(
            multiworld,
            priority_retry_2_state,
            prioritylocations,
            deprioritized_progression,
            single_player_placement=single_player,
            swap=False,
            on_place=mark_for_locking,
            name="Priority Retry 2",
            one_item_per_player=True,
            allow_partial=True,
        )

    if prioritylocations and deprioritized_progression:
        # retry with deprioritized items AND without one_item_per_player optimisation
        # Since we're leaving out the remaining regular progression now, we need to collect it into state first.
        priority_retry_3_state = sweep_from_pool(multiworld.state, regular_progression)
        fill_restrictive(
            multiworld,
            priority_retry_3_state,
            prioritylocations,
            deprioritized_progression,
            single_player_placement=single_player,
            swap=False,
            on_place=mark_for_locking,
            name="Priority Retry 3",
            one_item_per_player=False,
        )

    # restore original order of progitempool
    progitempool[:] = [item for item in progitempool if not item.location]


def run_deprioritized_patch() -> None:
    import Fill

    setattr(ItemClassification, "deprioritized", 0b10000)

    original_fill_restrictive = Fill.fill_restrictive

    def new_fill_restrictive(
        multiworld: MultiWorld,
        base_state: CollectionState,
        locations: typing.List[Location],
        item_pool: typing.List[Item],
        single_player_placement: bool = False,
        lock: bool = False,
        swap: bool = True,
        on_place: typing.Optional[typing.Callable[[Location], None]] = None,
        allow_partial: bool = False,
        allow_excluded: bool = False,
        one_item_per_player: bool = True,
        name: str = "Unknown",
    ):
        if name != "Priority":
            original_fill_restrictive(
                multiworld,
                base_state,
                locations,
                item_pool,
                single_player_placement,
                lock,
                swap,
                on_place,
                allow_partial,
                allow_excluded,
                one_item_per_player,
                name,
            )
            return

        new_priority_fill(
            multiworld, locations, item_pool, single_player=single_player_placement, mark_for_locking=on_place
        )

    Fill.fill_restrictive = new_fill_restrictive


def run_early_patch() -> None:
    if hasattr(ItemClassification, "deprioritized"):
        return

    run_deprioritized_patch()
