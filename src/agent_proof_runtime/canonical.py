"""Deterministic JSON bytes and SHA-256 helpers.

The proof schema deliberately accepts only the integer-safe subset of RFC 8785.
Floats are rejected instead of being serialized inconsistently across runtimes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

CANONICALIZATION_PROFILE = "RFC8785-JCS-INTEGER-PROFILE-v1"
HASH_ALGORITHM = "sha256"
SHA256_PREFIX = "sha256:"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class CanonicalizationError(ValueError):
    """Raised when a value is outside the canonical JSON profile."""


def _validate_string(value: str, path: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise CanonicalizationError(f"{path}: lone UTF-16 surrogate is not allowed")


def _sort_key(value: str) -> bytes:
    """RFC 8785 property ordering uses lexicographic UTF-16 code units."""

    return value.encode("utf-16-be")


def _serialize(value: Any, path: str) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise CanonicalizationError(
                f"{path}: integer exceeds the IEEE-754 safe integer range"
            )
        return str(value)
    if isinstance(value, float):
        raise CanonicalizationError(
            f"{path}: floating-point numbers are outside this profile"
        )
    if isinstance(value, str):
        _validate_string(value, path)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(
            _serialize(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise CanonicalizationError(f"{path}: object keys must be strings")
            _validate_string(key, f"{path}.<key>")
        entries = []
        for key in sorted(value, key=_sort_key):
            encoded_key = json.dumps(key, ensure_ascii=False, separators=(",", ":"))
            entries.append(f"{encoded_key}:{_serialize(value[key], f'{path}.{key}')}")
        return "{" + ",".join(entries) + "}"
    raise CanonicalizationError(
        f"{path}: unsupported JSON value type {type(value).__name__}"
    )


def canonicalize(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON for the accepted proof profile."""

    return _serialize(value, "$").encode("utf-8")


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_digest(data: bytes) -> str:
    return SHA256_PREFIX + sha256_bytes(data).hex()


def hash_json(value: Any) -> str:
    return sha256_digest(canonicalize(value))


def parse_sha256_digest(value: Any) -> bytes:
    if not isinstance(value, str) or not value.startswith(SHA256_PREFIX):
        raise ValueError("expected a sha256: prefixed digest")
    encoded = value[len(SHA256_PREFIX) :]
    if len(encoded) != 64:
        raise ValueError("SHA-256 digest must contain 64 hexadecimal characters")
    try:
        return bytes.fromhex(encoded)
    except ValueError as error:
        raise ValueError("SHA-256 digest contains non-hexadecimal characters") from error
