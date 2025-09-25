import collections
import typing
from logging import debug

from BaseClasses import Item, Location, MultiWorld, CollectionState
from worlds.ladx.LADXR import itempool


def balanced_shuffle(multiworld: MultiWorld, fill_locations: list[Location], itempool: list[Item]) -> list[Location]:
    balancing_factor = 0.5  # This would be a setting instead. Acts as a percentage. 0.0 is min, 1.0 is max.

    # First, we shuffle the location pool.
    multiworld.random.shuffle(fill_locations)

    # If balancing factor is 0, don't do any more unnecessary work.
    if balancing_factor == 0.0:
        return fill_locations

    # Balancing only has an effect if there is progression
    amount_of_progression = sum(1 for item in itempool if item.advancement)
    if not amount_of_progression:
        return fill_locations

    # If balancing factor is not 0, we split up the locations list by players.
    locations_per_player = collections.defaultdict(list)
    for location in fill_locations:
        locations_per_player[location.player].append(location)

    # shuffle the player order in the dict so that no player gets an inherent advantage.
    players_with_locations = list(locations_per_player.keys())
    multiworld.random.shuffle(players_with_locations)
    locations_per_player = {player: locations_per_player[player] for player in players_with_locations}

    # Grab some important values for later
    fill_location_counts = {player: len(locations) for player, locations in locations_per_player.items()}
    total_fill_locations = sum(fill_location_counts.values())

    # Now, the actual balancing begins.
    # We will have two sets of weights.

    # The first set of weights will be the number of progression items that are expected to end up in each world,
    # assuming full randomness.
    # Using this set of weights to shuffle the list will just, on average, just result in a random shuffle.

    expected_progression_counts_if_random = {
        player: fill_location_count / total_fill_locations * amount_of_progression
        for player, fill_location_count in fill_location_counts.items()
    }

    # The second set of weights is the number of progression items that would end up in each world if we tried to place
    # an equal amount of progression into each world.
    # This could be just one shared value for all worlds (number of progression items divided by number of slots), but
    # we have to make sure that we don't give any game more locations than it can hold.

    balanced_progression_counts = dict.fromkeys(fill_location_counts, 0)

    progression_to_distribute = amount_of_progression
    while True:
        for player, max_count in fill_location_counts.items():
            if balanced_progression_counts[player] == max_count:
                continue
            balanced_progression_counts[player] += 1
            progression_to_distribute -= 1
            if progression_to_distribute == 0:
                break
        else:  # have not distributed all progression yet
            continue
        break

    # Now, we use the balancing factor to interpolate between the "random" distribution and the "fair" distribution.
    weights_per_player = {
        player: random_count + (balanced_progression_counts[player] - random_count) * balancing_factor
        for player, random_count in expected_progression_counts_if_random.items()
    }

    debug(f"Balancing location order based on per-player check density: {weights_per_player}")

    # Finally, we use these weights to create the shuffled location list.
    # This means that, if the balancing_factor is any higher than 0.0, locations from smaller games will show up earlier
    # in the location list on average, meaning they receive more progression as a percentage of their location count.
    ret = []
    while locations_per_player:
        next_player = multiworld.random.choices(
            list(locations_per_player.keys()), weights=list(weights_per_player.values())
        )[0]
        next_bucket = locations_per_player[next_player]
        index_within_bucket = 0

        next_location = next_bucket.pop(index_within_bucket)
        if not next_bucket:
            del locations_per_player[next_player]
            del weights_per_player[next_player]
        ret.append(next_location)

    return ret


def distribute_items_restrictive_patch():
    import Fill

    # Since distribute_early_items has to be changed anyway, it's easiest to put this patch at the start of it.
    # We just redo the early work of Fill, at a slight performance cost.
    original_distribute_early_items = Fill.distribute_early_items

    def new_distribute_early_items(
        multiworld: MultiWorld, _fill_locations, *args, **kwargs
    ) -> typing.Tuple[typing.List[Location], typing.List[Item]]:
        itempool = sorted(multiworld.itempool)
        multiworld.random.shuffle(itempool)

        fill_locations = sorted(multiworld.get_unfilled_locations())
        fill_locations = balanced_shuffle(multiworld, sorted(fill_locations), itempool)

        original_order = fill_locations.copy()

        _, itempool = original_distribute_early_items(multiworld, fill_locations, *args, **kwargs)

        fill_locations = [location for location in original_order if not location.item]

        # The balanced shuffle PR has to *undo* its work later on, and this is a slight problem.
        # We will make a new remaining_fill that shuffles its input locations at the start.
        original_remaining_fill = Fill.remaining_fill

        def new_remaining_fill(
            multiworld: MultiWorld, locations: typing.List[Location], *args, **kwargs
        ):
            multiworld.random.shuffle(locations)
            original_remaining_fill(multiworld, locations, *args, **kwargs)

        Fill.remaining_fill = new_remaining_fill

        return fill_locations, itempool

    Fill.distribute_early_items = new_distribute_early_items


def run_early_patch() -> None:
    distribute_items_restrictive_patch()
