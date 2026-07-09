from __future__ import annotations

import re
import sys
from pathlib import Path


FENCE_RE = re.compile(r"^```(?:\s*\S.*)?$")


def markdown_files(repo_root: Path) -> list[Path]:
    files = [repo_root / "README.md"]
    files.extend(sorted((repo_root / "docs").rglob("*.md")))
    return [path for path in files if path.exists()]


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_fence = False
    fence_start_line: int | None = None
    previous_line_opened_fence = False

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not FENCE_RE.match(line):
            previous_line_opened_fence = False
            continue

        if in_fence:
            if previous_line_opened_fence:
                errors.append(
                    f"{path}:{line_number}: nested fenced code block detected"
                )
            in_fence = False
            fence_start_line = None
            previous_line_opened_fence = False
        else:
            in_fence = True
            fence_start_line = line_number
            previous_line_opened_fence = True

    if in_fence and fence_start_line is not None:
        errors.append(
            f"{path}:{fence_start_line}: unbalanced fenced code block opened here"
        )

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    for path in markdown_files(repo_root):
        errors.extend(check_file(path))

    if errors:
        print("Markdown fence check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Markdown fence check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
