"""Local multi-provider mail API."""

from .client import Maily, SyncMaily

# Keep in sync with the `version` in pyproject.toml and with the standalone
# client at client/maily_client.py (it reads its own __version__ for auto-updates).
__version__ = "0.9.1"  # x-release-please-version

__all__ = ["Maily", "SyncMaily", "__version__"]
