from BaseClasses import Region, Item, ItemClassification
from worlds.AutoWorld import World


class TestWorld(World):
    game = "TestWorld"
    topology_present = False

    item_name_to_id = {
        "Left Room Key 1": 319872598000,
        "Left Room Key 2": 319872598001,
        "Left Room Key 3": 319872598002,
        "Left Room Key 4": 319872598003,
        "Left Room Key 5": 319872598004,
        "Right Room Key 1": 319872598005,
        "Right Room Key 2": 319872598006,
        "Right Room Key 3": 319872598007,
        "Right Room Key 4": 319872598008,
        "Right Room Key 5": 319872598009,
        "Useless": 319872598010,
        "Victory": 319872598050,
    }
    location_name_to_id = {
        "Starting Room Location 1": 319872598000,
        "Starting Room Location 2": 319872598001,
        "Starting Room Location 3": 319872598002,
        "Starting Room Location 4": 319872598003,
        "Starting Room Location 5": 319872598004,
        "Left Room Location 1": 319872598005,
        "Right Room Location 1": 319872598006,
        "Right Room Location 2": 319872598007,
        "Right Room Location 3": 319872598008,
        "Right Room Location 4": 319872598009,
        "Right Room Location 5": 319872598010,
        "Final Location": 319872598050,
    }

    def create_item(self, name):
        if name == "Nothing":
            return Item(name, ItemClassification.filler, self.item_name_to_id[name], self.player)

        return Item(name, ItemClassification.progression, self.item_name_to_id[name], self.player)

    def create_regions(self):
        entry = Region("Menu", self.player, self.multiworld)

        starting_room = Region("Starting Room", self.player, self.multiworld)
        starting_room.add_locations({
            "Starting Room Location 1": 319872598000,
            "Starting Room Location 2": 319872598001,
            "Starting Room Location 3": 319872598002,
            "Starting Room Location 4": 319872598003,
            "Starting Room Location 5": 319872598004,
        })

        left_room = Region("Left Room", self.player, self.multiworld)
        left_room.add_locations({
            "Left Room Location 1": 319872598005,
        })

        right_room = Region("Right Room", self.player, self.multiworld)
        right_room.add_locations({
            "Right Room Location 1": 319872598006,
            "Right Room Location 2": 319872598007,
            "Right Room Location 3": 319872598008,
            "Right Room Location 4": 319872598009,
            "Right Room Location 5": 319872598010,
            "Final Location": 319872598050,
        })

        self.multiworld.regions += [entry, left_room, right_room]

        entry.connect(starting_room)
        starting_room.connect(left_room, rule=lambda state: state.has_all([
            "Left Room Key 1",
            "Left Room Key 2",
            "Left Room Key 3",
            "Left Room Key 4",
            "Left Room Key 5"
        ], self.player))
        starting_room.connect(right_room, rule=lambda state: state.has_all([
            "Right Room Key 1",
            "Right Room Key 2",
            "Right Room Key 3",
            "Right Room Key 4",
            "Right Room Key 5"
        ], self.player))

        for item in self.item_name_to_id:
            if item == "Victory":
                self.multiworld.get_location("Final Location", self.player).place_locked_item(
                    self.create_item("Victory"))
            else:
                self.multiworld.itempool.append(self.create_item(item))

        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

#  This test world fails on seed 80818606476286984189 when there is absolutely a valid item placement.
