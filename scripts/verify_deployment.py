"""Validate production deployment files without building an image."""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "Dockerfile",
    ".dockerignore",
    "render.yaml",
    ".streamlit/config.toml",
    "requirements.txt",
    "frontend/app.py",
)

DOCKERFILE_REQUIREMENTS = (
    "FROM python:3.12",
    "USER appuser",
    "EXPOSE 8501",
    "HEALTHCHECK",
    "/_stcore/health",
    "${PORT:-8501}",
    "frontend/app.py",
)

DOCKERIGNORE_REQUIREMENTS = (
    ".env",
    ".venv",
    "__pycache__",
    "data/*.db",
    ".streamlit/secrets.toml",
)

RENDER_REQUIREMENTS = (
    "runtime: docker",
    "dockerfilePath: ./Dockerfile",
    "healthCheckPath: /_stcore/health",
    "OLLAMA_API_KEY",
    "sync: false",
)


def read(relative_path: str) -> str:
    """Read a required deployment file."""

    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def check_required_files() -> list[str]:
    """Return missing deployment paths."""

    return [
        relative_path
        for relative_path in REQUIRED_FILES
        if not (PROJECT_ROOT / relative_path).exists()
    ]


def missing_values(
    content: str,
    expected_values: tuple[str, ...],
) -> list[str]:
    """Return expected snippets absent from a file."""

    return [value for value in expected_values if value not in content]


def check_for_embedded_secrets() -> list[str]:
    """Detect suspicious hard-coded credentials in deployment files."""

    failures: list[str] = []

    patterns = (
        re.compile(r"gh[pousr]_[A-Za-z0-9]+"),
        re.compile(r"github_pat_[A-Za-z0-9_]+"),
        re.compile(r"OLLAMA_API_KEY\s*[:=]\s*\S{8,}"),
    )

    for relative_path in (
        "Dockerfile",
        "render.yaml",
        ".streamlit/config.toml",
    ):
        content = read(relative_path)

        for pattern in patterns:
            if pattern.search(content):
                failures.append(f"Possible credential in {relative_path}")

    return failures


def main() -> int:
    """Run all deployment-file checks."""

    missing_files = check_required_files()

    if missing_files:
        for path in missing_files:
            print(f"[FAILED] Missing deployment file: {path}")
        return 1

    checks = (
        (
            "Dockerfile",
            DOCKERFILE_REQUIREMENTS,
        ),
        (
            ".dockerignore",
            DOCKERIGNORE_REQUIREMENTS,
        ),
        (
            "render.yaml",
            RENDER_REQUIREMENTS,
        ),
    )

    failed = False

    for relative_path, expected_values in checks:
        absent = missing_values(
            read(relative_path),
            expected_values,
        )

        if absent:
            failed = True

            for value in absent:
                print(f"[FAILED] {relative_path} missing: {value}")
        else:
            print(f"[OK] {relative_path}")

    secret_failures = check_for_embedded_secrets()

    if secret_failures:
        failed = True

        for failure in secret_failures:
            print(f"[FAILED] {failure}")
    else:
        print("[OK] No embedded deployment credentials detected")

    if failed:
        return 1

    print("[PASSED] Deployment configuration verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
