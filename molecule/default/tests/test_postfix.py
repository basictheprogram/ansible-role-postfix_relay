# Copyright (c) 2026 Real Time Enterprises, Inc.
"""Rendered-content and service-state tests for the postfix_relay scenario.

Covers what test_config.py's existence/permission checks don't: actual
main.cf/mynetworks/aliases content (from converge.yml's fixture values)
and the postfix service itself. One assertion focus per test function.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from testinfra.host import Host


def test_postfix_service_running(host: Host) -> None:
    service = host.service("postfix")
    assert service.is_running


def test_postfix_service_enabled(host: Host) -> None:
    service = host.service("postfix")
    assert service.is_enabled


def test_main_cf_myhostname(host: Host) -> None:
    content = host.file("/etc/postfix/main.cf").content_string
    assert "myhostname = molecule.local" in content


def test_main_cf_mydestination(host: Host) -> None:
    content = host.file("/etc/postfix/main.cf").content_string
    assert "mydestination = relay.molecule.local, molecule.local, localhost" in content


def test_main_cf_mynetworks_points_at_file(host: Host) -> None:
    content = host.file("/etc/postfix/main.cf").content_string
    assert "mynetworks = $config_directory/mynetworks" in content


def test_main_cf_masquerade_domains(host: Host) -> None:
    content = host.file("/etc/postfix/main.cf").content_string
    assert "masquerade_domains = masquerade.molecule.local" in content


def test_mynetworks_file_contents(host: Host) -> None:
    content = host.file("/etc/postfix/mynetworks").content_string
    assert "192.168.100.0/24" in content
    assert "172.16.0.0/16" in content


def test_aliases_root_delivery(host: Host) -> None:
    content = host.file("/etc/aliases").content_string
    assert "root:           admin@molecule.local" in content
