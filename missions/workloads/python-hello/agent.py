from pathlib import Path


output = Path("/output")
output.mkdir(parents=True, exist_ok=True)
(output / "hello.txt").write_text(
    "hello from a gVisor-isolated agent\n",
    encoding="utf-8",
)
