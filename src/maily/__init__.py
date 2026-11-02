"""Local multi-provider mail API."""

from .client import MailTMAPI

# Keep in sync with the `version` in pyproject.toml and with the standalone
# client at client/client.py (it reads its own __version__ for auto-updates).
__version__ = "0.3.0"

__all__ = ["MailTMAPI", "__version__"]
