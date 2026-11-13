from __future__ import annotations

import os

import pytest

# The release ships a real PostHog project token, so telemetry is switched off
# for the whole test session: the suite must never phone home. Tests that
# exercise telemetry opt back in explicitly via ``telemetry_enabled=True``.
os.environ["MAILY_TELEMETRY_ENABLED"] = "false"

# Compatibility shim for pytest-benchmark with pytest >= 9.0
if not hasattr(pytest.Item, "_nodeid"):
    pytest.Item._nodeid = property(lambda self: self.nodeid)  # type: ignore[attr-defined]
