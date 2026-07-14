"""RFC 6962 Merkle Tree Hash implementation."""

from __future__ import annotations

from collections.abc import Sequence

from .canonical import parse_sha256_digest, sha256_bytes


def _largest_power_of_two_less_than(value: int) -> int:
    if value < 2:
        raise ValueError("value must be at least two")
    return 1 << ((value - 1).bit_length() - 1)


def merkle_tree_hash(leaves: Sequence[bytes]) -> bytes:
    """Return Merkle Tree Hash exactly as defined by RFC 6962 section 2.1."""

    count = len(leaves)
    if count == 0:
        return sha256_bytes(b"")
    if count == 1:
        return sha256_bytes(b"\x00" + leaves[0])
    split = _largest_power_of_two_less_than(count)
    left = merkle_tree_hash(leaves[:split])
    right = merkle_tree_hash(leaves[split:])
    return sha256_bytes(b"\x01" + left + right)


def merkle_root_from_step_hashes(step_hashes: Sequence[str]) -> str:
    leaves = [parse_sha256_digest(value) for value in step_hashes]
    return "sha256:" + merkle_tree_hash(leaves).hex()
