import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from Utils import parse_yaml
from worlds.AutoWorld import TestableWorld

if TYPE_CHECKING:
    from worlds.AutoWorld import World


class TestGenerateYamlTemplates(unittest.TestCase):
    old_testable_worlds: dict[str, TestableWorld]

    def setUp(self) -> None:
        import worlds.AutoWorld

        self.old_testable_worlds = worlds.AutoWorld.AutoWorldRegister.testable_worlds

    def tearDown(self) -> None:
        import worlds.AutoWorld

        worlds.AutoWorld.AutoWorldRegister.testable_worlds = self.old_testable_worlds

        if "World: with colon" in worlds.AutoWorld.AutoWorldRegister.testable_worlds:
            del worlds.AutoWorld.AutoWorldRegister.testable_worlds["World: with colon"]

    def test_name_with_colon(self) -> None:
        from Options import generate_yaml_templates
        from worlds.AutoWorld import AutoWorldRegister
        from worlds.AutoWorld import World

        class WorldWithColon(World):
            game = "World: with colon"
            item_name_to_id = {}
            location_name_to_id = {}

        AutoWorldRegister.testable_worlds = {WorldWithColon.game: TestableWorld(WorldWithColon)}
        with TemporaryDirectory(f"archipelago_{__name__}") as temp_dir:
            generate_yaml_templates(temp_dir)
            path: Path
            for path in Path(temp_dir).iterdir():
                self.assertTrue(path.is_file())
                self.assertTrue(path.suffix == ".yaml")
                with path.open(encoding="utf-8") as f:
                    try:
                        data = parse_yaml(f)
                    except:
                        f.seek(0)
                        print(f"Error in {path.name}:\n{f.read()}")
                        raise
                    self.assertIn("game", data)
                    self.assertIn(":", data["game"])
                    self.assertIn(data["game"], data)
                    self.assertIsInstance(data[data["game"]], dict)
