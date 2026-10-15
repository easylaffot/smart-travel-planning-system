"""Run safe structural checks for the completed travel-planning project."""

import importlib
import json
import sys
from pathlib import Path

from smart_travel_planner.config.settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "frontend/app.py",
    "frontend/backend.py",
    "frontend/components.py",
    "frontend/result_components.py",
    "src/smart_travel_planner/agents/factory.py",
    "src/smart_travel_planner/crew/task_factory.py",
    "src/smart_travel_planner/crew/travel_crew.py",
    "src/smart_travel_planner/services/planning_service.py",
    "src/smart_travel_planner/services/revision_service.py",
    "src/smart_travel_planner/storage/plan_repository.py",
    "src/smart_travel_planner/workflow/travel_workflow.py",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "pyproject.toml",
]

REQUIRED_IMPORTS = [
    "smart_travel_planner.agents",
    "smart_travel_planner.crew",
    "smart_travel_planner.models",
    "smart_travel_planner.providers",
    "smart_travel_planner.services",
    "smart_travel_planner.storage",
    "smart_travel_planner.tools",
    "smart_travel_planner.workflow",
    "frontend.backend",
    "frontend.exporters",
    "frontend.result_components",
]


def check_required_paths() -> list[str]:
    missing = []

    for relative_path in REQUIRED_PATHS:
        if not (PROJECT_ROOT / relative_path).exists():
            missing.append(relative_path)

    return missing


def check_imports() -> list[str]:
    failed = []

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            failed.append(f"{module_name}: {exc}")

    return failed


def check_devcontainer() -> str | None:
    path = PROJECT_ROOT / ".devcontainer" / "devcontainer.json"

    if not path.exists():
        return "devcontainer.json is missing"

    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"devcontainer.json is invalid: {exc}"

    return None


def main() -> int:
    settings = get_settings()

    print(f"[OK] Application: {settings.app_name}")
    print(f"[OK] Python: {sys.version.split()[0]}")
    print(f"[OK] Ollama configured: {'yes' if settings.ollama_is_configured() else 'no'}")

    missing_paths = check_required_paths()

    if missing_paths:
        for path in missing_paths:
            print(f"[FAILED] Missing path: {path}")
        return 1

    print(f"[OK] Required project paths: {len(REQUIRED_PATHS)}")

    failed_imports = check_imports()

    if failed_imports:
        for failure in failed_imports:
            print(f"[FAILED] Import: {failure}")
        return 1

    print(f"[OK] Required imports: {len(REQUIRED_IMPORTS)}")

    devcontainer_error = check_devcontainer()

    if devcontainer_error:
        print(f"[FAILED] {devcontainer_error}")
        return 1

    print("[OK] Development container configuration is valid")
    print("[PASSED] Project structural verification completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
