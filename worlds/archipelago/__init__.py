from BaseClasses import Item, MultiWorld, Region, Location, Entrance, ItemClassification
from .Items import game_table, version_table, games_per_version, \
    archipelago_version_items, archipelago_version_free_checks, archipelago_version_game_unlocks, \
    archipelago_version_game_checks, archipelago_version_game_items, associated_checks_per_item, \
    archipelago_version_names, archipelago_game_free_checks, version_mode_locations, archipelago_game_free_check_to_game
from .Options import ArchipelagoVersionOptions, is_option_enabled
from ..AutoWorld import World


class ArchipelagoVersionWorld(World):
    """
    An idle game which sends a check every thirty seconds, up to one hundred checks.
    """
    game = "ArchipelagoVersion"
    topology_present = False
    data_version = 1

    option_definitions = ArchipelagoVersionOptions

    item_name_to_id = {"Progressive Archipelago Version": 195690000,
                       "Free trial of the critically acclaimed MMORPG Final Fantasy XIV, including the entirety of A Realm Reborn and the award winning Heavensward expansion up to level 60 with no restrictions on playtime!": 195690001}

    item_name_to_id.update(archipelago_version_game_items)
    item_name_to_id.update(archipelago_version_items)

    location_name_to_id = {}

    location_name_to_id.update(archipelago_version_free_checks)
    location_name_to_id.update(archipelago_version_game_checks)
    location_name_to_id.update(archipelago_game_free_checks)

    def generate_basic(self):   
        if is_option_enabled(self.multiworld, self.player, "VersionMode"):
            for location, item in archipelago_version_game_unlocks.items():
                self.multiworld.get_location(location, self.player).place_locked_item(self.create_item(item))

            earliest_version = 4
            for i, v in enumerate(archipelago_version_free_checks):
                if i < earliest_version:
                    self.multiworld.get_location(v, self.player).place_locked_item(self.create_item("Progressive Archipelago Version"))
                else:
                    self.multiworld.itempool.append(self.create_item("Progressive Archipelago Version"))
                    self.multiworld.get_location(v, self.player).item_rule = lambda item: item.name != "Progressive Archipelago Version"

        else:
            self.multiworld.itempool += [self.create_item(i) for i in game_table if i != self.starting_game]
            self.multiworld.itempool.append(self.create_item("Free trial of the critically acclaimed MMORPG Final Fantasy XIV, including the entirety of A Realm Reborn and the award winning Heavensward expansion up to level 60 with no restrictions on playtime!", ItemClassification.filler))

            print(self.starting_game)

            self.multiworld.push_precollected(self.create_item(self.starting_game))

    def create_version_lambda(self, ind):
        return lambda state: state.has("Progressive Archipelago Version", self.player, ind)

    def create_all_games_lambda(self):
        return lambda state: state.has_all(game_table.keys(), self.player)

    def create_game_lambda(self, item):
        return lambda s: s.has(item, self.player)

    def fill_slot_data(self) -> dict:
        return {
            "item_check_associations": associated_checks_per_item,
            "progressive_equivalents": {list(version_table).index(v): archipelago_version_items[n] for v, n in archipelago_version_names.items()},
            "version_mode": is_option_enabled(self.multiworld, self.player, "VersionMode")
        }

    def set_rules(self):
        for location in self.multiworld.get_locations(self.player):
            location = location.name
            if "Berserker Multiworld" in location:
                continue

            if location in archipelago_game_free_check_to_game:
                self.multiworld.get_location(location, self.player).access_rule = self.create_game_lambda(archipelago_game_free_check_to_game[location])
                continue
            required_version = location[20:]
            required_version = required_version.split(" ")[0]
            v = tuple(int(i) for i in required_version.split("."))

            vers = list(version_table)
            ind = vers.index(v)

            self.multiworld.get_location(location, self.player).access_rule = self.create_version_lambda(ind)

        if is_option_enabled(self.multiworld, self.player, "VersionMode"):
            self.multiworld.completion_condition[self.player] = self.create_version_lambda(ind)
        else:
            self.multiworld.completion_condition[self.player] = self.create_all_games_lambda()

    def create_item(self, name: str, classification=ItemClassification.progression) -> Item:
        return Item(name, classification, self.item_name_to_id[name], self.player)

    def create_regions(self):
        if is_option_enabled(self.multiworld, self.player, "VersionMode"):
            self.multiworld.regions += [
                create_region(self.multiworld, self.player, 'Menu', None, ['Entrance to ArchipelagoVersion']),
                create_region(self.multiworld, self.player, 'ArchipelagoVersion', version_mode_locations)
            ]
        else:
            games_minus_starting_game = archipelago_game_free_checks.copy()
            games = list(games_minus_starting_game.keys())
            self.multiworld.per_slot_randoms[self.player].shuffle(games)
            starting_game_check = games[0]
            self.starting_game = archipelago_game_free_check_to_game[starting_game_check]
            del games_minus_starting_game[starting_game_check]

            self.multiworld.regions += [
                create_region(self.multiworld, self.player, 'Menu', None, ['Entrance to ArchipelagoVersion']),
                create_region(self.multiworld, self.player, 'ArchipelagoVersion', archipelago_game_free_checks)
            ]

        # link up our region with the entrance we just made
        self.multiworld.get_entrance('Entrance to ArchipelagoVersion', self.player)\
            .connect(self.multiworld.get_region('ArchipelagoVersion', self.player))

    def get_filler_item_name(self) -> str:
        return "Nothing"


def create_region(world: MultiWorld, player: int, name: str, locations=None, exits=None):
    region = Region(name, player, world)
    if locations:
        for location_name in locations.keys():
            location = ArchipelagoVersionLocation(player, location_name, locations[location_name], region)
            region.locations.append(location)

    if exits:
        for _exit in exits:
            region.exits.append(Entrance(player, _exit, region))

    return region


class ArchipelagoVersionItem(Item):
    game = "ArchipelagoVersion"


class ArchipelagoVersionLocation(Location):
    game: str = "ArchipelagoVersion"
