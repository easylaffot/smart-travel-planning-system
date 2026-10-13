"""Fail when secret-like files are tracked by Git."""

import subprocess
import sys

FORBIDDEN_EXACT = {".env"}
FORBIDDEN_SUFFIXES = (".db", ".sqlite", ".sqlite3")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print("[INFO] Git repository not initialized; tracked-file scan skipped")
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    unsafe = [
        path for path in tracked_files()
        if path in FORBIDDEN_EXACT or path.endswith(FORBIDDEN_SUFFIXES)
    ]
    if unsafe:
        print("[FAILED] Unsafe tracked files:")
        for path in unsafe:
            print(f" - {path}")
        return 1
    print("[PASSED] No tracked .env or runtime database files found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
