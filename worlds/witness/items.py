"""
Defines progression, junk and event items for The Witness
"""
import copy
from dataclasses import dataclass
from typing import Optional, Dict, List, Set

from BaseClasses import Item, MultiWorld, ItemClassification
from .Options import get_option_value, is_option_enabled, the_witness_options

from .locations import ID_START, WitnessPlayerLocations
from .player_logic import WitnessPlayerLogic
from .static_logic import ItemDefinition, DoorItemDefinition, ProgressiveItemDefinition, ItemCategory, \
    StaticWitnessLogic, WeightedItemDefinition
from .utils import build_weighted_int_list
from logging import info, warning


@dataclass()
class ItemData:
    """
    ItemData for an item in The Witness
    """
    ap_code: Optional[int]
    definition: ItemDefinition
    classification: ItemClassification
    local_only: bool = False


class WitnessItem(Item):
    """
    Item from the game The Witness
    """
    game: str = "The Witness"


class StaticWitnessItems:
    """
    Class that handles Witness items independent of world settings
    """
    item_data: Dict[str, ItemData] = {}
    item_groups: Dict[str, List[str]] = {}

    # Useful items that are treated specially at generation time and should not be automatically added to the player's
    #   item list during get_progression_items.
    special_usefuls: List[str] = ["Puzzle Skip"]

    def __init__(self):
        for item_name, definition in StaticWitnessLogic.all_items.items():
            ap_item_code = definition.local_code + ID_START
            classification: ItemClassification = ItemClassification.filler
            local_only: bool = False

            if definition.category is ItemCategory.SYMBOL:
                classification = ItemClassification.progression
                StaticWitnessItems.item_groups.setdefault("Symbols", []).append(item_name)
            elif definition.category is ItemCategory.DOOR:
                classification = ItemClassification.progression
                StaticWitnessItems.item_groups.setdefault("Doors", []).append(item_name)
            elif definition.category is ItemCategory.LASER:
                classification = ItemClassification.progression
                StaticWitnessItems.item_groups.setdefault("Lasers", []).append(item_name)
            elif definition.category is ItemCategory.USEFUL:
                classification = ItemClassification.useful
            elif definition.category is ItemCategory.FILLER:
                if item_name in ["Energy Fill (Small)"]:
                    local_only = True
                classification = ItemClassification.filler
            elif definition.category is ItemCategory.TRAP:
                classification = ItemClassification.trap
            elif definition.category is ItemCategory.JOKE:
                classification = ItemClassification.filler

            StaticWitnessItems.item_data[item_name] = ItemData(ap_item_code, definition,
                                                               classification, local_only)

    @staticmethod
    def get_item_to_door_mappings() -> Dict[int, List[int]]:
        output: Dict[int, List[int]] = {}
        for item_name, item_data in {name: data for name, data in StaticWitnessItems.item_data.items()
                                     if isinstance(data.definition, DoorItemDefinition)}.items():
            item = StaticWitnessItems.item_data[item_name]
            output[item.ap_code] = [int(hex_string, 16) for hex_string in item_data.definition.panel_id_hexes]
        return output


class WitnessPlayerItems:
    """
    Class that defines Items for a single world
    """

    def __init__(self, multiworld: MultiWorld, player: int, logic: WitnessPlayerLogic, locat: WitnessPlayerLocations):
        """Adds event items after logic changes due to options"""

        self._world: MultiWorld = multiworld
        self._player_id: int = player
        self._logic: WitnessPlayerLogic = logic
        self._locations: WitnessPlayerLocations = locat

        # Duplicate the static item data, then make any player-specific adjustments to classification.
        self.item_data: Dict[str, ItemData] = copy.deepcopy(StaticWitnessItems.item_data)

        # Remove all progression items that aren't actually in the game.
        self.item_data = {name: data for (name, data) in self.item_data.items()
                          if data.classification is not ItemClassification.progression or
                          name in logic.PROG_ITEMS_ACTUALLY_IN_THE_GAME}

        # Adjust item classifications based on game settings.
        eps_shuffled = get_option_value(self._world, self._player_id, "shuffle_EPs") != 0
        for item_name, item_data in self.item_data.items():
            if not eps_shuffled and item_name in ["Monastery Garden Entry (Door)", "Monastery Shortcuts"]:
                # Downgrade doors that only gate progress in EP shuffle.
                item_data.classification = ItemClassification.useful
            elif item_name in ["River Monastery Shortcut (Door)", "Jungle & River Shortcuts",
                               "Monastery Shortcut (Door)",
                               "Orchard Second Gate (Door)"]:
                # Downgrade doors that don't gate progress.
                item_data.classification = ItemClassification.useful

        # Build the mandatory item list.
        self._mandatory_items: Dict[str, int] = {}

        # Add progression items to the mandatory item list.
        for item_name, item_data in {name: data for (name, data) in self.item_data.items()
                                     if data.classification == ItemClassification.progression}.items():
            if isinstance(item_data.definition, ProgressiveItemDefinition):
                num_progression = len(self._logic.MULTI_LISTS[item_name])
                self._mandatory_items[item_name] = num_progression
            else:
                self._mandatory_items[item_name] = 1

        # Add setting-specific useful items to the mandatory item list.
        for item_name, item_data in {name: data for (name, data) in self.item_data.items()
                                     if data.classification == ItemClassification.useful}.items():
            if item_name in StaticWitnessItems.special_usefuls:
                continue
            elif item_name == "Energy Capacity":
                self._mandatory_items[item_name] = 3
            elif isinstance(item_data.classification, ProgressiveItemDefinition):
                self._mandatory_items[item_name] = len(item_data.mappings)
            else:
                self._mandatory_items[item_name] = 1

        # Add event items to the item definition list for later lookup.
        for event_location in self._locations.EVENT_LOCATION_TABLE:
            location_name = logic.EVENT_ITEM_PAIRS[event_location]
            self.item_data[location_name] = ItemData(None, ItemDefinition(0, ItemCategory.EVENT),
                                                     ItemClassification.progression, False)

    def get_mandatory_items(self) -> Dict[str, int]:
        """
        Returns the list of items that must be in the pool for the game to successfully generate.
        """
        return self._mandatory_items

    def get_filler_items(self, total_pool_size: int, slots_to_fill: int) -> Dict[str, int]:
        """
        Generates a list of filler items of the given length.
        """
        if slots_to_fill <= 0:
            return {}

        # First, place joke items, since there are a known quantity of those.
        joke_items: Dict[str, int]
        joke_items = {name: 1 for (name, data) in self.item_data.items()
                      if data.definition.category is ItemCategory.JOKE}

        # If there's more joke items than slots to fill, scale the list down to the available number and just return
        #   that.
        num_joke_items = sum(joke_items.values())
        if num_joke_items > slots_to_fill:
            warning("Too few slots to place all joke items.")
            return zip(joke_items.keys(), build_weighted_int_list(joke_items.values(), slots_to_fill))
        elif num_joke_items == slots_to_fill:
            return joke_items

        slots_to_fill -= num_joke_items

        # Next, determine the contents of the filler pool. In order to keep the ratio of energy fills consistent across
        #   configurations, we want to treat placed items as small energy fills, since solving a check gives the player
        #   a small fill as a bonus. In order to do so, we generate the filler pool as if there were no non-filler items
        #   placed, then remove small fills equal to the number of non-filler items.
        # First, build the core list of filler items, as configured.
        filler_items: Dict[str, int]
        filler_items = {name: data.definition.weight if isinstance(data.definition, WeightedItemDefinition) else 1
                        for (name, data) in self.item_data.items() if data.definition.category is ItemCategory.FILLER}

        # Next, add traps to the filler pool, if needed.
        trap_weight: float = get_option_value(self._world, self._player_id, "trap_percentage") / 100
        if trap_weight > 0:
            # Since the filler array is of length 1, scale trap_weight to keep the ratio of traps to filler the same.
            trap_weight = 1 / (sum(filler_items.values()) * (1 - trap_weight))
            trap_items = {name: data.definition.weight if isinstance(data.definition, WeightedItemDefinition) else 1
                          for (name, data) in self.item_data.items() if data.definition.category is ItemCategory.TRAP}
            filler_items.update({name: base_weight * trap_weight / sum(trap_items.values())
                                 for name, base_weight in trap_items.items() if base_weight > 0})

        # Scale the list of filler items to the total size of the pool.
        filler_items = dict(zip(filler_items.keys(), build_weighted_int_list(filler_items.values(), total_pool_size)))

        # Remove small fills.
        if "Energy Fill (Small)" in filler_items.keys():
            small_fills_to_remove: int = total_pool_size - slots_to_fill
            if filler_items["Energy Fill (Small)"] > small_fills_to_remove:
                filler_items["Energy Fill (Small)"] -= small_fills_to_remove
            else:
                # If there are more items than small fills, remove small fills entirely, then scale the remaining item
                #   list to the output size.
                info("There were too few small fills ({0}) in the junk pool to match the number of placed items ({1}). "
                     "Junk pool composition will be affected.".format(filler_items["Energy Fill (Small)"],
                                                                      small_fills_to_remove))
                filler_items.pop("Energy Fill (Small)")
                filler_items = dict(zip(filler_items.keys(), build_weighted_int_list(filler_items.values(),
                                                                                     slots_to_fill)))

        output: Dict[str, int] = {}
        output.update(joke_items)
        output.update(filler_items)

        return output

    def get_early_items(self) -> List[str]:
        """
        Returns items that are ideal for placing on extremely early checks, like the tutorial gate.
        """
        output: Set[str] = set()
        if "shuffle_symbols" not in the_witness_options.keys() \
                or is_option_enabled(self._world, self._player_id, "shuffle_symbols"):
            if get_option_value(self._world, self._player_id, "shuffle_doors") > 0:
                output = {"Dots", "Black/White Squares", "Symmetry"}
            else:
                output = {"Dots", "Black/White Squares", "Symmetry", "Shapers", "Stars"}

            if is_option_enabled(self._world, self._player_id, "shuffle_discarded_panels"):
                if get_option_value(self._world, self._player_id, "puzzle_randomization") == 1:
                    output.add("Arrows")
                else:
                    output.add("Triangles")

            # Replace progressive items with their parents.
            output = {StaticWitnessLogic.get_parent_progressive_item(item) for item in output}

        # Remove items that are mentioned in any plando options. (Hopefully, in the future, plando will get resolved
        #   before create_items so that we'll be able to check placed items instead of just removing all items mentioned
        #   regardless of whether or not they actually wind up being manually placed.
        for plando_setting in self._world.plando_items[self._player_id]:
            if plando_setting.get("from_pool", True):
                for item_setting_key in [key for key in ["item", "items"] if key in plando_setting]:
                    if type(plando_setting[item_setting_key]) is str:
                        output -= {plando_setting[item_setting_key]}
                    elif type(plando_setting[item_setting_key]) is dict:
                        output -= {item for item, weight in plando_setting[item_setting_key].items() if weight}
                    else:
                        # Assume this is some other kind of iterable.
                        for inner_item in plando_setting[item_setting_key]:
                            if type(inner_item) is str:
                                output -= {inner_item}
                            elif type(inner_item) is dict:
                                output -= {item for item, weight in inner_item.items() if weight}

        # Sort the output for consistency across versions if the implementation changes but the logic does not.
        return sorted(list(output))

    def get_door_ids_in_pool(self) -> List[int]:
        """
        Returns the total set of all door IDs that are controlled by items in the pool.
        """
        output: List[int] = []
        for item_name, item_data in {name: data for name, data in self.item_data.items()
                                     if isinstance(data.definition, DoorItemDefinition)}.items():
            output += [int(hex_string, 16) for hex_string in item_data.definition.panel_id_hexes]
        return output

    def get_symbol_ids_not_in_pool(self) -> List[int]:
        """
        Returns the item IDs of symbol items that were defined in the configuration file but are not in the pool.
        """
        return [data.ap_code for name, data in StaticWitnessItems.item_data.items()
                if name not in self.item_data.keys() and data.definition.category is ItemCategory.SYMBOL]

    def get_progressive_item_ids_in_pool(self) -> Dict[int, List[int]]:
        output: Dict[int, List[int]] = {}
        for item_name, quantity in {name: quantity for name, quantity in self._mandatory_items.items()}.items():
            item = self.item_data[item_name]
            if isinstance(item.definition, ProgressiveItemDefinition):
                # Note: we need to reference the static table here rather than the player-specific one because the child
                #   items were removed from the pool when we pruned out all progression items not in the settings.
                output[item.ap_code] = [StaticWitnessItems.item_data[child_item].ap_code
                                        for child_item in item.definition.child_item_names]
        return output
