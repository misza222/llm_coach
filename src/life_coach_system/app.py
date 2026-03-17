"""
Package-level app entry point.

Delegates to the root app.py launch logic.
This module is referenced by the project.scripts entry point.
"""

import importlib.util
import sys
from pathlib import Path


def main() -> None:
    """Load and run the root app.py main() function."""
    root_app = Path(__file__).parents[3] / "app.py"
    spec = importlib.util.spec_from_file_location("_root_app", root_app)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load app.py from {root_app}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_root_app"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    module.main()
