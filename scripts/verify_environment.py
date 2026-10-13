"""Verify safe Phase 1 configuration without printing secret values."""

import sys

from smart_travel_planner.config.settings import get_settings


def main() -> int:
    settings = get_settings()
    print(f"[OK] Application: {settings.app_name}")
    print(f"[OK] Environment: {settings.app_env}")
    print(f"[OK] Ollama base URL: {settings.ollama_base_url}")
    if settings.ollama_is_configured():
        print("[OK] Ollama Cloud key and model are configured")
    else:
        print("[INFO] Ollama key/model not configured yet; required in Phase 3")
    print("[PASSED] Phase 1 environment validation completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
