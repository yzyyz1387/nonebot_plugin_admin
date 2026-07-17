from __future__ import annotations

from time import monotonic

_TTL_SECONDS = 120
_command_kicks: dict[tuple[str, str], tuple[int, bool, float]] = {}


def _cleanup_expired(now: float) -> None:
    expired = [key for key, (_, _, created_at) in _command_kicks.items() if now - created_at > _TTL_SECONDS]
    for key in expired:
        _command_kicks.pop(key, None)


def remember_command_kick(group_id: int, user_id: int, operator_id: int, *, reject_add_request: bool) -> None:
    now = monotonic()
    _cleanup_expired(now)
    _command_kicks[(str(group_id), str(user_id))] = (int(operator_id), bool(reject_add_request), now)


def pop_command_kick(group_id: int, user_id: int) -> tuple[int, bool] | None:
    now = monotonic()
    _cleanup_expired(now)
    item = _command_kicks.pop((str(group_id), str(user_id)), None)
    if item is None:
        return None
    operator_id, reject_add_request, _ = item
    return operator_id, reject_add_request
