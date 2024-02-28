game_table = {
    "A Link to the Past": (0, 0, 0),
    "Factorio": (0, 0, 2),
    "Minecraft": (0, 1, 0),
    "Subnautica": (0, 1, 5),
    "Ocarina of Time": (0, 1, 7),
    "Risk of Rain 2": (0, 1, 7),
    "Slay the Spire": (0, 1, 7),
    "Timespinner": (0, 1, 9),
    "Super Metroid": (0, 2, 0),
    "Secret of Evermore": (0, 2, 0),
    "Final Fantasy": (0, 2, 1),
    "Rogue Legacy": (0, 2, 3),
    "Super Mario 64": (0, 2, 4),
    "Raft": (0, 2, 4),
    "VVVVVV": (0, 2, 4),
    "SMZ3": (0, 3, 0),
    "ArchipIDLE": (0, 3, 0),
    "Meritous": (0, 3, 0),
    "ChecksFinder": (0, 3, 0),
    "Hollow Knight": (0, 3, 1),
    "The Witness": (0, 3, 2),
    "Sonic Adventure 2 Battle": (0, 3, 2),
    "Starcraft 2 Wings of Liberty": (0, 3, 2),
    "Dark Souls III": (0, 3, 4),
    "Donkey Kong Country 3": (0, 3, 4),
    "Super Mario World": (0, 3, 6),
    "Pokemon Red and Blue": (0, 3, 6),
    "Hylics 2": (0, 3, 6),
    "Overcooked! 2": (0, 3, 6),
    "Zillion": (0, 3, 6),
    "Lufia II Ancient Cave": (0, 3, 7),
    "Blasphemous": (0, 4, 0),
    "Wargroove": (0, 4, 0),
    "Stardew Valley": (0, 4, 0),
    "The Legend of Zelda": (0, 4, 0),
    "The Messenger": (0, 4, 0),
    "Kingdom Hearts 2": (0, 4, 0),
    "Links Awakening DX": (0, 4, 0),
    "Clique": (0, 4, 0),
    "Adventure": (0, 4, 0),
}


def get_ap_version_offset(v):
    return v[0] + 50 * v[1] + 50 * 50 * v[2]


version_table = {v: 1 for k, v in game_table.items()}.keys()
games_per_version = {version: sum(1 for v in game_table.values() if v == version) for version in version_table}

archipelago_version_names = {v: f"Archipelago Version {v[0]}.{v[1]}.{v[2]}" for v in version_table if v != (0,0,0)}
archipelago_version_names[(0,0,0)] = "Berserker Multiworld"

archipelago_version_items = {archipelago_version_names[v]: 175690000 + get_ap_version_offset(v)
                             for v in version_table}
archipelago_version_free_checks = {}

associated_checks_per_item = {}

for v in version_table:
    new_check = f"{archipelago_version_names[v]} Free Check"

    archipelago_version_free_checks[new_check] = 175690000 + get_ap_version_offset(v)

    associated_checks_per_item.setdefault(archipelago_version_names[v], []).append(new_check)

archipelago_version_game_unlocks = {}

current_counts = {}

for game, v in game_table.items():
    current_counts.setdefault(v, 0)
    current_counts[v] += 1
    c = current_counts[v]
    new_check_name = f"{archipelago_version_names[v]} Game {c}"
    archipelago_version_game_unlocks[new_check_name] = game

    associated_checks_per_item.setdefault(archipelago_version_names[v], []).append(new_check_name)

archipelago_version_game_checks = {}
archipelago_version_game_items = {}

ver_count = -1
game_count = -1

for vc, gc in archipelago_version_game_unlocks.items():
    ver_count += 1
    game_count += 1

    archipelago_version_game_checks[vc] = 185690000 + ver_count
    archipelago_version_game_items[gc] = 185690000 + game_count

archipelago_game_free_checks = {}
archipelago_game_free_check_to_game = {}

for game, version in game_table.items():
    game_count += 1
    archipelago_game_free_checks[game + " Free Check"] = 185691000 + game_count

    archipelago_game_free_check_to_game[game + " Free Check"] = game

    associated_checks_per_item.setdefault(game, []).append(game + " Free Check")

all_checks = archipelago_version_free_checks.copy()
all_checks.update(archipelago_version_game_checks)
all_checks.update(archipelago_game_free_checks)

all_items = archipelago_version_items.copy()
all_items.update(archipelago_version_game_items)

associated_checks_per_item = {all_items[k]: [all_checks[c] for c in v]
                                            for k, v in associated_checks_per_item.items()}

game_count = -1


archipelago_version_free_checks = {k.replace("Archipelago Version 0.0.0", "Berserker Multiworld"):
                                   v for k, v in archipelago_version_free_checks.items()}
archipelago_version_items = {k.replace("Archipelago Version 0.0.0", "Berserker Multiworld"):
                                   v for k, v in archipelago_version_items.items()}
archipelago_version_game_checks = {k.replace("Archipelago Version 0.0.0", "Berserker Multiworld"):
                                   v for k, v in archipelago_version_game_checks.items()}
archipelago_version_game_items = {k.replace("Archipelago Version 0.0.0", "Berserker Multiworld"):
                                   v for k, v in archipelago_version_game_items.items()}
archipelago_version_game_unlocks = {k.replace("Archipelago Version 0.0.0", "Berserker Multiworld"):
                                   v for k, v in archipelago_version_game_unlocks.items()}

version_mode_locations = archipelago_version_free_checks.copy()
version_mode_locations.update(archipelago_version_game_checks)