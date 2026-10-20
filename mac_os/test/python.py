"""Explicit module registration. No SDK/model imports are needed for boundary tests."""

import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "runtime"))
suite = unittest.defaultTestLoader.discover(
    str(root / "runtime/adapters/personal_voice/test"), pattern="test_*.py"
)
if suite.countTestCases() == 0:
    raise SystemExit("no_python_tests")
raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
