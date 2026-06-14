"""Windows desktop system utilities for Diablo."""

from system.apps import close_application, launch_application, list_running_applications
from system.clipboard import read_clipboard
from system.volume import get_volume_percent, set_volume_percent

__all__ = [
    "close_application",
    "get_volume_percent",
    "launch_application",
    "list_running_applications",
    "read_clipboard",
    "set_volume_percent",
]
