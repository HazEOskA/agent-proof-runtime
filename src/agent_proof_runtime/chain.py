"""Linear event hash chain."""

from __future__ import annotations

import copy
from typing import Any

from .canonical import CanonicalizationError, hash_json

GENESIS_HASH = "sha256:" + ("00" * 32)
EVENT_KEYS = frozenset(
    {
        "index",
        "type",
        "input",
        "output",
        "details",
        "input_hash",
        "output_hash",
        "details_hash",
        "previous_step_hash",
        "step_hash",
    }
)


def _step_payload(
    *,
    index: int,
    event_type: str,
    input_hash: str,
    output_hash: str,
    details_hash: str,
    previous_step_hash: str,
) -> dict[str, Any]:
    return {
        "details_hash": details_hash,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "previous_step_hash": previous_step_hash,
        "step_index": index,
        "type": event_type,
    }


def build_event(
    *,
    index: int,
    event_type: str,
    event_input: Any,
    event_output: Any,
    details: Any,
    previous_step_hash: str,
) -> dict[str, Any]:
    if index < 0:
        raise ValueError("event index cannot be negative")
    if not event_type:
        raise ValueError("event type cannot be empty")

    input_hash = hash_json(event_input)
    output_hash = hash_json(event_output)
    details_hash = hash_json(details)
    step_hash = hash_json(
        _step_payload(
            index=index,
            event_type=event_type,
            input_hash=input_hash,
            output_hash=output_hash,
            details_hash=details_hash,
            previous_step_hash=previous_step_hash,
        )
    )
    return {
        "index": index,
        "type": event_type,
        "input": event_input,
        "output": event_output,
        "details": details,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "details_hash": details_hash,
        "previous_step_hash": previous_step_hash,
        "step_hash": step_hash,
    }


class EventChain:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def append(
        self,
        event_type: str,
        *,
        event_input: Any,
        event_output: Any,
        details: Any,
    ) -> dict[str, Any]:
        previous = self._events[-1]["step_hash"] if self._events else GENESIS_HASH
        event = build_event(
            index=len(self._events),
            event_type=event_type,
            event_input=event_input,
            event_output=event_output,
            details=details,
            previous_step_hash=previous,
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._events)


def verify_event_chain(events: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(events, list):
        return ["events must be an array"]

    expected_previous = GENESIS_HASH
    for expected_index, event in enumerate(events):
        label = f"event[{expected_index}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        keys = frozenset(event)
        if keys != EVENT_KEYS:
            missing = sorted(EVENT_KEYS - keys)
            unknown = sorted(keys - EVENT_KEYS)
            if missing:
                errors.append(f"{label} is missing keys: {', '.join(missing)}")
            if unknown:
                errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
            continue

        if event["index"] != expected_index:
            errors.append(f"{label} has a non-sequential index")
        if not isinstance(event["type"], str) or not event["type"]:
            errors.append(f"{label} has an invalid type")
        if event["previous_step_hash"] != expected_previous:
            errors.append(f"{label} does not point to the previous step hash")

        try:
            expected_input_hash = hash_json(event["input"])
            expected_output_hash = hash_json(event["output"])
            expected_details_hash = hash_json(event["details"])
            expected_step_hash = hash_json(
                _step_payload(
                    index=expected_index,
                    event_type=event["type"],
                    input_hash=expected_input_hash,
                    output_hash=expected_output_hash,
                    details_hash=expected_details_hash,
                    previous_step_hash=expected_previous,
                )
            )
        except (CanonicalizationError, RecursionError, TypeError, ValueError) as error:
            errors.append(f"{label} cannot be canonicalized: {error}")
            expected_previous = event.get("step_hash", expected_previous)
            continue

        comparisons = (
            ("input_hash", expected_input_hash),
            ("output_hash", expected_output_hash),
            ("details_hash", expected_details_hash),
            ("step_hash", expected_step_hash),
        )
        for field, expected in comparisons:
            if event[field] != expected:
                errors.append(f"{label} {field} mismatch")
        expected_previous = event["step_hash"]

    return errors
