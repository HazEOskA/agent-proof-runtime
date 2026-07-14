from __future__ import annotations

import unittest

from agent_proof_runtime.chain import EventChain, verify_event_chain
from agent_proof_runtime.merkle import merkle_tree_hash


class EventChainTests(unittest.TestCase):
    def test_chain_verifies_and_detects_tampering(self) -> None:
        chain = EventChain()
        chain.append(
            "task.started",
            event_input={"task": "demo"},
            event_output={"accepted": True},
            details={"actor": "test"},
        )
        chain.append(
            "task.finished",
            event_input={},
            event_output={"passed": True},
            details={"actor": "test"},
        )
        events = chain.events
        self.assertEqual(verify_event_chain(events), [])

        events[0]["output"]["accepted"] = False
        errors = verify_event_chain(events)
        self.assertTrue(any("output_hash mismatch" in error for error in errors))
        self.assertTrue(any("step_hash mismatch" in error for error in errors))


class MerkleTests(unittest.TestCase):
    def test_empty_tree_vector(self) -> None:
        self.assertEqual(
            merkle_tree_hash([]).hex(),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_single_leaf_vector(self) -> None:
        self.assertEqual(
            merkle_tree_hash([b"a"]).hex(),
            "022a6979e6dab7aa5ae4c3e5e45f7e977112a7e63593820dbec1ec738a24f93c",
        )

    def test_three_leaf_vector_does_not_duplicate_last_leaf(self) -> None:
        self.assertEqual(
            merkle_tree_hash([b"a", b"b", b"c"]).hex(),
            "36642e73c2540ab121e3a6bf9545b0a24982cd830eb13d3cd19de3ce6c021ec1",
        )


if __name__ == "__main__":
    unittest.main()
