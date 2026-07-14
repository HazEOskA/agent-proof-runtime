from __future__ import annotations

import unittest

from agent_proof_runtime.canonical import (
    MAX_SAFE_INTEGER,
    CanonicalizationError,
    canonicalize,
)


class CanonicalizationTests(unittest.TestCase):
    def test_canonical_object_has_no_whitespace_and_stable_order(self) -> None:
        value = {"z": [True, None, "zażółć"], "a": 7}
        self.assertEqual(
            canonicalize(value),
            '{"a":7,"z":[true,null,"zażółć"]}'.encode("utf-8"),
        )

    def test_keys_are_sorted_by_utf16_code_units(self) -> None:
        value = {"\ufffd": 2, "\U0001f600": 1}
        self.assertEqual(
            canonicalize(value),
            '{"😀":1,"�":2}'.encode("utf-8"),
        )

    def test_float_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonicalize({"amount": 1.5})

    def test_unsafe_integer_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonicalize({"amount": MAX_SAFE_INTEGER + 1})


if __name__ == "__main__":
    unittest.main()
