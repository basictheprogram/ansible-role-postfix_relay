# Copyright (c) 2026 Real Time Enterprises, Inc.
"""Config-file existence/permission tests for the postfix_relay scenario.

Parametrized existence checks over CONFIG_FILES (full absolute paths --
see _data.py for why this role skips the config_dir fixture pattern).
Content assertions live in test_postfix.py, one function per file/setting
pair -- never combine an existence check and a content check in one test.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._data import CONFIG_FILES

if TYPE_CHECKING:
    from testinfra.host import Host


@pytest.mark.parametrize("filename", CONFIG_FILES)
def test_config_file_exists(host: Host, filename: str) -> None:
    f = host.file(filename)
    assert f.exists
    assert f.is_file


def test_main_cf_permissions(host: Host) -> None:
    f = host.file("/etc/postfix/main.cf")
    assert f.user == "root"
    assert f.group == "root"
    assert f.mode == 0o644
