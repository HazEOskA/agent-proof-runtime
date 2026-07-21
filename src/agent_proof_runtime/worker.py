"""Fixed demo agent executed by the development sandbox backend."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _emit(event_type: str, event_input: dict, event_output: dict, details: dict) -> None:
    print(
        json.dumps(
            {
                "type": event_type,
                "input": event_input,
                "output": event_output,
                "details": details,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )


def main() -> int:
    artifact_path = Path("artifact") / "hello.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=False)
    content = "Agent Proof Runtime v0.1\nsandbox run completed\n"
    artifact_path.write_text(content, encoding="utf-8")
    written = artifact_path.read_bytes()
    digest = "sha256:" + hashlib.sha256(written).hexdigest()
    _emit(
        "agent.file_written",
        {"path": artifact_path.as_posix()},
        {"bytes_written": len(written), "sha256": digest},
        {"agent": "built-in-demo", "capability": "workspace.write"},
    )

    observed = artifact_path.read_text(encoding="utf-8")
    passed = observed == content
    _emit(
        "agent.test_completed",
        {"check": "artifact_content_matches"},
        {"passed": passed},
        {"agent": "built-in-demo", "capability": "workspace.read"},
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
