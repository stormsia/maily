from __future__ import annotations

import pytest

# Compatibility shim for pytest-benchmark with pytest >= 9.0
if not hasattr(pytest.Item, "_nodeid"):
    pytest.Item._nodeid = property(lambda self: self.nodeid)  # type: ignore[attr-defined]
