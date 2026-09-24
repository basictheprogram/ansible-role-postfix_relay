# Copyright (c) 2026 Real Time Enterprises, Inc.
"""Package installation tests for the postfix_relay Molecule scenario.

Parametrized over DEBIAN_PACKAGES/REDHAT_PACKAGES in _data.py, picking the
right list for whichever OS family the target host actually is. Works
unmodified once those two lists are filled in -- no per-role edits needed
here, unlike test_config.py.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._data import DEBIAN_PACKAGES, REDHAT_DISTROS, REDHAT_PACKAGES

if TYPE_CHECKING:
    from testinfra.host import Host


def _expected_packages(host: Host) -> list[str]:
    dist: str = host.system_info.distribution.lower()
    return REDHAT_PACKAGES if dist in REDHAT_DISTROS else DEBIAN_PACKAGES


@pytest.fixture
def expected_packages(host: Host) -> list[str]:
    return _expected_packages(host)


def test_expected_packages_installed(host: Host, expected_packages: list[str]) -> None:
    for package_name in expected_packages:
        assert host.package(package_name).is_installed
