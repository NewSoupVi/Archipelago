"""
Defines the rules by which locations can be accessed,
depending on the items received
"""
import operator
from functools import reduce
from typing import TYPE_CHECKING, NamedTuple, Optional

from rule_builder.rules import CanReachRegion, False_, Has, HasFromList, Rule, True_

from .data import static_logic as static_witness_logic
from .data.definition_classes import WitnessRule
from .data.utils import entrance_is_reachable
from .player_logic import WitnessPlayerLogic

if TYPE_CHECKING:
    from . import WitnessWorld


class SimpleItemRepresentation(NamedTuple):
    item_name: str
    item_count: int


def _can_do_panel_hunt(world: "WitnessWorld") -> Rule["WitnessWorld"]:
    required = world.panel_hunt_required_count
    return Has("+1 Panel Hunt", required)


def _has_lasers(amount: int, world: "WitnessWorld", redirect_required: bool) -> Rule["WitnessWorld"]:
    if redirect_required:
        return HasFromList("+1 Laser", "+1 Laser (Redirected)", count=amount)

    return HasFromList("+1 Laser", "+1 Laser (Unredirected)", count=amount)


def _can_do_expert_pp2(world: "WitnessWorld") -> Rule["WitnessWorld"]:
    """
    For Expert PP2, you need a way to access PP2 from the front, and a separate way from the back.
    This condition is quite complicated. We'll attempt to evaluate it as lazily as possible.
    """

    front_access = entrance_is_reachable(world, "Keep 2nd Pressure Plate", "Keep") & CanReachRegion("Keep")
    shadows_shortcut = entrance_is_reachable(world, "Keep 4th Pressure Plate", "Shadows")
    fourth_to_third = entrance_is_reachable(world, "Keep 3rd Pressure Plate", "Keep 4th Pressure Plate")
    tower_to_pp4 = entrance_is_reachable(world, "Keep 4th Pressure Plate", "Keep Tower")
    tower_shortcut = entrance_is_reachable(world, "Keep", "Keep Tower")
    tower_access_from_hedges = entrance_is_reachable(world, "Keep 4th Maze", "Keep Tower")
    hedge_4_shortcut = entrance_is_reachable(world, "Keep 4th Maze", "Keep")
    hedge_3_to_4 = entrance_is_reachable(world, "Keep 4th Maze", "Keep 3rd Maze")
    hedge_3_shortcut = entrance_is_reachable(world, "Keep 3rd Maze", "Keep")
    hedge_2_to_3 = entrance_is_reachable(world, "Keep 3rd Maze", "Keep 2nd Maze")
    hedge_1_to_2_or_shortcut = entrance_is_reachable(world, "Keep 2nd Maze", "Keep")

    return (
        front_access
        & fourth_to_third
        & (
            shadows_shortcut
            | (
                tower_to_pp4
                & (
                    tower_shortcut
                    | (
                        tower_access_from_hedges
                        & (
                            hedge_4_shortcut
                            | (hedge_3_to_4 & (hedge_3_shortcut | (hedge_2_to_3 & hedge_1_to_2_or_shortcut)))
                        )
                    )
                )
            )
        )
    )


def _can_do_theater_to_tunnels(world: "WitnessWorld") -> Rule["WitnessWorld"]:
    """
    To do Tunnels Theater Flowers EP, you need to quickly move from Theater to Tunnels.
    This condition is a little tricky. We'll attempt to evaluate it as lazily as possible.
    """

    # Checking for access to Theater is not necessary, as solvability of Tutorial Video is checked in the other half
    # of the Theater Flowers EP condition.

    tunnels_to_windmill = entrance_is_reachable(world, "Tunnels", "Windmill Interior")
    theater_to_windmill = entrance_is_reachable(world, "Theater", "Windmill Interior")

    windmill_entrance = entrance_is_reachable(world, "Outside Windmill", "Windmill Interior")
    tunnels_to_town = entrance_is_reachable(world, "Tunnels", "Town")

    return (
        (tunnels_to_windmill & theater_to_windmill)  # direct to Tunnel via direct path from Theater
        | (tunnels_to_windmill & windmill_entrance)  # access to Tunnel via Town (windmill)
        | tunnels_to_town  # Access to Tunnel via Town (shortcut)
    )


def _has_item(item: str, world: "WitnessWorld", player_logic: WitnessPlayerLogic) -> Rule["WitnessWorld"]:
    """
    Convert a single element of a WitnessRule into a CollectionRule, unless it is referring to an item,
    in which case we return it as an item-count pair ("SimpleItemRepresentation"). This allows some optimisation later.
    """

    assert item not in static_witness_logic.ENTITIES_BY_HEX, "Requirements can no longer contain entity hexes directly."

    if item in player_logic.REFERENCE_LOGIC.ALL_REGIONS_BY_NAME:
        return CanReachRegion(item)
    if item == "7 Lasers":
        laser_req = world.options.mountain_lasers.value
        return _has_lasers(laser_req, world, False)
    if item == "7 Lasers + Redirect":
        laser_req = world.options.mountain_lasers.value
        return _has_lasers(laser_req, world, True)
    if item == "11 Lasers":
        laser_req = world.options.challenge_lasers.value
        return _has_lasers(laser_req, world, False)
    if item == "11 Lasers + Redirect":
        laser_req = world.options.challenge_lasers.value
        return _has_lasers(laser_req, world, True)
    if item == "Entity Hunt":
        # Right now, panel hunt is the only type of entity hunt. This may need to be changed later
        return _can_do_panel_hunt(world)
    if "Eggs" in item:
        return Has("Egg", int(item.split(" ")[0]))
    if item == "PP2 Weirdness":
        return _can_do_expert_pp2(world)
    if item == "Theater to Tunnels":
        return _can_do_theater_to_tunnels(world)

    actual_item = static_witness_logic.get_parent_progressive_item(item)
    needed_amount = player_logic.PARENT_ITEM_COUNT_PER_BASE_ITEM[item]

    return Has(actual_item, needed_amount)

def _meets_item_requirements(requirements: WitnessRule, world: "WitnessWorld") -> Optional[Rule["WitnessWorld"]]:
    """
    Converts a WitnessRule into a Rule Builder Rule.
    """
    if requirements == frozenset({frozenset()}):
        return None

    rule_conversion = [[_has_item(item, world, world.player_logic) for item in subset] for subset in requirements]

    return reduce(operator.or_, [reduce(operator.and_, subset, True_()) for subset in rule_conversion], False_())

def make_rule(entity_hex: str, world: "WitnessWorld") -> Optional[Rule["WitnessWorld"]]:
    """
    Lambdas are created in a for loop so values need to be captured
    """
    entity_req = world.player_logic.REQUIREMENTS_BY_HEX[entity_hex]

    return _meets_item_requirements(entity_req, world)


def make_region_rule(region_name: str, world: "WitnessWorld") -> Rule["WitnessWorld"]:
    """
    Lambdas are created in a for loop so values need to be captured
    """
    return CanReachRegion(region_name)


def set_rules(world: "WitnessWorld") -> None:
    """
    Sets all rules for all locations
    """

    for location in world.player_locations.CHECK_LOCATION_TABLE:
        real_location = location

        if location in world.player_locations.EVENT_LOCATION_TABLE:
            entity_hex_or_region_name = world.player_logic.EVENT_ITEM_PAIRS[location][1]
            if entity_hex_or_region_name in static_witness_logic.ALL_REGIONS_BY_NAME:
                location_obj = world.get_location(location)
                world.set_rule(location_obj, make_region_rule(entity_hex_or_region_name, world))
                continue

            real_location = static_witness_logic.ENTITIES_BY_HEX[entity_hex_or_region_name]["checkName"]

        associated_entity = world.player_logic.REFERENCE_LOGIC.ENTITIES_BY_NAME[real_location]
        entity_hex = associated_entity["entity_hex"]

        rule = make_rule(entity_hex, world)
        if rule is None:
            continue

        location_obj = world.get_location(location)
        world.set_rule(location_obj, rule)

    world.set_completion_rule(Has("Victory"))
