"""Proof Bundle serialization and whole-bundle integrity helpers."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .canonical import hash_json

SCHEMA_VERSION = "apr.proof-bundle.v0.1"
MAX_BUNDLE_BYTES = 10 * 1024 * 1024


class BundleFormatError(ValueError):
    pass


def compute_bundle_hash(bundle: dict[str, Any]) -> str:
    preimage = copy.deepcopy(bundle)
    integrity = preimage.get("integrity")
    if not isinstance(integrity, dict):
        raise BundleFormatError("integrity must be an object")
    integrity.pop("bundle_hash", None)
    return hash_json(preimage)


def write_bundle(path: Path, bundle: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(
        bundle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BundleFormatError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_bundle(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise BundleFormatError(f"cannot read bundle: {error}") from error
    if size > MAX_BUNDLE_BYTES:
        raise BundleFormatError("bundle exceeds the 10 MiB size limit")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise BundleFormatError(f"invalid bundle JSON: {error}") from error
    if not isinstance(value, dict):
        raise BundleFormatError("bundle root must be an object")
    return value
