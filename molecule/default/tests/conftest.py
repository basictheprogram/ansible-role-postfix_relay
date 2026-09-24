# Copyright (c) 2026 Real Time Enterprises, Inc.
"""Session-scoped pytest fixtures for the postfix_relay Molecule scenario.

No shared fixture is needed here -- this role has no OS-varying config
directory (see _data.py), so there's nothing analogous to the example
config_dir fixture in the packaged skeleton to adapt.
"""
from __future__ import annotations
