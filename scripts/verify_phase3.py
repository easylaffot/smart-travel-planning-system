"""Offline verification for Phase 3 agent, task, and crew assembly."""

import argparse
import sys

from crewai import LLM, Process

from smart_travel_planner.agents import TravelAgentFactory
from smart_travel_planner.config.settings import Settings, get_settings
from smart_travel_planner.crew import TravelCrewFactory
from smart_travel_planner.services import OllamaLLMFactory
from smart_travel_planner.utils.exceptions import SmartTravelPlannerError


def offline_llm() -> LLM:
    """Create a client object that is never called by this script."""

    return LLM(
        model="ollama/offline-verification",
        base_url="http://localhost:11434",
        api_key="offline-verification-key",
        temperature=0.0,
        max_tokens=256,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Phase 3 without executing the travel crew."
    )
    parser.add_argument(
        "--live-llm",
        action="store_true",
        help=("Construct the configured Ollama LLM client. This still does not call kickoff."),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()

    try:
        if args.live_llm:
            llm = OllamaLLMFactory(settings=settings).create()
            mode = "configured Ollama client"
        else:
            isolated_settings = Settings(
                _env_file=None,
                app_env="test",
                crew_verbose=False,
                crew_cache_enabled=False,
            )
            settings = isolated_settings
            llm = offline_llm()
            mode = "offline client"

        factory = TravelCrewFactory(
            llm=llm,
            settings=settings,
        )
        crew = factory.build()

        print(f"[OK] LLM mode: {mode}")
        print(f"[OK] Agents: {len(factory.agents)}")
        print(f"[OK] Tasks: {len(factory.tasks)}")
        print(
            f"[OK] Process: {'sequential' if crew.process == Process.sequential else crew.process}"
        )
        print("[OK] Kickoff executed: no")
        print("[OK] Live prompt sent: no")

        for key, agent in factory.agents.items():
            tools = [tool.name for tool in agent.tools]
            print(f"[OK] Agent: {key}; role={agent.role}; tools={tools}")

        expected_agents = TravelAgentFactory.EXPECTED_AGENT_KEYS

        if set(factory.agents) != expected_agents:
            print("[FAILED] Agent keys do not match expectations.")
            return 1

        print("[PASSED] Phase 3 crew assembly verified")
        return 0

    except SmartTravelPlannerError as exc:
        print(f"[FAILED] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
