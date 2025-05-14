from worlds.AutoWorld import AutoWorldRegister

from .patches import *
from .patches import patch_module_names
from . import patches as patches_module


def run_early_patches() -> None:
    for patch_module in patch_module_names:
        run_early_patch_function = getattr(getattr(patches_module, patch_module), "run_early_patch", None)
        if run_early_patch_function is not None:
            run_early_patch_function()


def run_fill_patches() -> None:
    for patch_module in patch_module_names:
        run_fill_patch_function = getattr(getattr(patches_module, patch_module), "run_fill_patch", None)
        if run_fill_patch_function is not None:
            run_fill_patch_function()


def hook_fill_patches() -> None:
    import Fill

    original_distribute_items_restrictive = Fill.distribute_items_restrictive

    def patched_distribute_items_restrictive(*args, **kwargs):
        run_fill_patches()
        return original_distribute_items_restrictive(*args, **kwargs)

    Fill.distribute_items_restrictive = patched_distribute_items_restrictive


def hook_early_patches() -> None:
    # This function must somehow ensure that the patch is run after all the other worlds are loaded,
    # ideally at the very earliest point possible.

    # Currently we do this by monkeypatching AutoWorldRegister.world_types.items,
    # as it's the earliest hookable code after world loads have finished.

    class PatchedDict(dict):
        patched = False

        def items(self):
            if not self.patched:
                self.patched = True
                hook_fill_patches()
                run_early_patches()
            return super().items()

    AutoWorldRegister.world_types = PatchedDict(AutoWorldRegister.world_types)


hook_early_patches()