# Copyright (c) 2026 Real Time Enterprises, Inc.
"""Shared test constants for the postfix_relay Molecule scenario.

This role doesn't vary its config paths by OS family (Debian and Ubuntu
both write to /etc/postfix and /etc/aliases), and it writes to more than
one directory, so CONFIG_FILES holds full absolute paths rather than the
CONFIG_DIR_BY_FAMILY pattern used by roles with a single OS-varying
config directory.
"""
from __future__ import annotations

# 1. OS-family detection.
REDHAT_DISTROS: frozenset[str] = frozenset({"redhat", "centos", "rocky", "almalinux", "fedora"})

# 2. Packages this role should install, per OS family. Identical list on
# both currently-supported families (vars/Debian.yml == vars/Ubuntu.yml).
# This role does not support RedHat -- REDHAT_PACKAGES stays empty.
DEBIAN_PACKAGES: list[str] = [
    "postfix",
    "postfix-pcre",
    "make",
    "dovecot-core",
    "dovecot-sqlite",
    "sqlite3",
]
REDHAT_PACKAGES: list[str] = []

# 3. Config files this role renders (converge.yml's fixture: template mode,
# sasl_type/tls_rsa unset), for existence/permission checks.
CONFIG_FILES: list[str] = [
    "/etc/postfix/main.cf",
    "/etc/postfix/mynetworks",
    "/etc/aliases",
]
