import logging
from typing import List

from BaseClasses import Item, ItemClassification, Location, Region, MultiWorld, CollectionState
from worlds.AutoWorld import World
from .options import ArchipelagoLockerOptions
from ..generic.Rules import add_rule


class ArchipelagoLockerWorld(World):
    game = "ArchipelagoLocker"

    item_name_to_id = {"Free trial of the critically acclaimed MMORPG Final Fantasy XIV, including the entirety of A Realm Reborn and the award winning Heavensward expansion up to level 60 with no restrictions on playtime!": 195690001}
    location_name_to_id = {"Starting Game": 195690001}

    game_item_to_id = dict()
    game_location_to_id = dict()

    options_dataclass = ArchipelagoLockerOptions

    own_itempool: List[Item]

    representative_world = 0

    @classmethod
    def stage_generate_early(cls, multiworld: MultiWorld):
        from worlds import network_data_package

        world_names = sorted({(world.game, player) for player, world in multiworld.worlds.items()})

        for i, (world_name, world_player) in enumerate(world_names):
            if world_name == cls.game:
                if cls.representative_world:
                    raise RuntimeError("There can only be one ArchipelagoLocker world per multiworld.")
                cls.representative_world = world_player
                continue

            cls.game_location_to_id[world_name + " Free Check"] = 195691000 + i
            cls.game_item_to_id[world_name] = 195691000 + i

        cls.location_name_to_id |= cls.game_location_to_id
        cls.item_name_to_id |= cls.game_item_to_id

        network_data_package["games"][cls.game] = cls.get_data_package_data()

        for world in multiworld.worlds.values():
            if world.game == "Stardew Valley":
                world.force_first_month_once_all_early_items_are_found = lambda: None

    def create_items(self):
        for item_name in self.item_name_to_id:
            own_itempool.append(self.create_item(item_name))

    def create_regions(self):
        menu_region = Region("Menu", self.player, self.multiworld)
        menu_region.add_locations(self.location_name_to_id, ArchipelagoLockerLocation)

        self.multiworld.regions.append(menu_region)

    def set_rules(self):
        for item_name, item_id in self.game_item_to_id.items():
            location = self.multiworld.get_location(item_name + " Free Check", self.player)
            location.access_rule = lambda state, item=item_name: state.has(item, self.player)

        victory_items = list(self.game_item_to_id)
        self.multiworld.completion_condition[self.player] = lambda state: state.has_all(victory_items, self.player)

    @classmethod
    def stage_pre_fill(cls, multiworld: MultiWorld):
        warning = False
        for player, world in multiworld.worlds.items():
            if world.game == cls.game:
                continue

            state = CollectionState(multiworld)
            state.sweep_for_events(locations=multiworld.get_locations(player))

            reachable_locs = [loc for loc in multiworld.get_reachable_locations(state, player)
                              if loc.address and not loc.item]

            if len(reachable_locs) < 10:
                logging.warning(f"Player {player}'s {world.game} slot has only {len(reachable_locs)} early locations:"
                                f" {reachable_locs}.")
                warning = True

        if warning:
            logging.warning("A small sphere 1 will severely increase the change of generation failure"
                            " when ArchipelagoLocker is used.")

        for player, world in multiworld.worlds.items():
            if world.game == cls.game:
                continue
            for location in multiworld.get_locations(player):
                add_rule(location, lambda state, game_name=world.game: state.has(game_name, cls.representative_world))

    def create_item(self, name: str):
        classif = ItemClassification.progression if name in self.game_item_to_id else ItemClassification.filler
        return ArchipelagoLockerItem(name, classif, self.item_name_to_id[name], self.player)


class ArchipelagoLockerItem(Item):
    game = "ArchipelagoLocker"


class ArchipelagoLockerLocation(Location):
    game = "ArchipelagoLocker"
