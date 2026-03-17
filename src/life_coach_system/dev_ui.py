"""
Package-level dev UI entry point.

Delegates to the root dev_ui.py launch logic.
This module is referenced by the project.scripts entry point.
"""

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    """Load and run the root dev_ui.py main() function."""
    root_app = Path(__file__).parents[3] / "dev_ui.py"
    spec = importlib.util.spec_from_file_location("_root_dev_ui", root_app)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load app.py from {root_app}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_root_dev_ui"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    module.main()
