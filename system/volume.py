"""Windows master volume control."""

from __future__ import annotations

import logging

from core.exceptions import ToolExecutionError

logger = logging.getLogger("diablo.system.volume")


def _get_endpoint():
    try:
        from ctypes import cast, POINTER

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError as exc:
        raise ToolExecutionError(
            "pycaw is required for volume control",
            details="pip install pycaw",
        ) from exc

    devices = AudioUtilities.GetSpeakers()
    if devices is None:
        raise ToolExecutionError("No audio output device found")

    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def get_volume_percent() -> int:
    """Return the current master volume as an integer percentage."""
    endpoint = _get_endpoint()
    scalar = endpoint.GetMasterVolumeLevelScalar()
    return int(round(float(scalar) * 100))


def set_volume_percent(level: int) -> int:
    """Set master volume to a percentage between 0 and 100."""
    if not 0 <= level <= 100:
        raise ToolExecutionError("Volume must be between 0 and 100")

    endpoint = _get_endpoint()
    endpoint.SetMasterVolumeLevelScalar(level / 100.0, None)
    logger.info("Set volume to %d%%", level)
    return level
