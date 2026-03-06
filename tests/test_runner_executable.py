from __future__ import annotations

import sys
from pathlib import Path

from ai_code_repair.runner.runner import _build_pytest_cmd


def test_pytest_cmd_uses_sys_executable():
    cmd = _build_pytest_cmd(Path("/tmp/junit.xml"), [])
    assert cmd[0] == sys.executable
