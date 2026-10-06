"""Composite resolver preserving legacy Creative Claw acceptance while adding
generic motion-organ acceptance."""
from __future__ import annotations

from . import motion_video_resolver, video_resolver


def resolve_accepted_video_for_serve(root, address: str):
    legacy_error = None
    try:
        return video_resolver.resolve_accepted_video_for_serve(root, address)
    except Exception as exc:
        legacy_error = exc
    try:
        return motion_video_resolver.resolve_accepted_motion_video_for_serve(root, address)
    except Exception as generic_error:
        raise ValueError(
            f"No accepted video resolver could verify address. "
            f"legacy={type(legacy_error).__name__}; generic={type(generic_error).__name__}"
        ) from generic_error
