"""Offline tests for sequential travel-crew assembly."""

from crewai import LLM, Crew, Process

from smart_travel_planner.config.settings import Settings
from smart_travel_planner.crew import TravelCrewFactory


def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        crew_verbose=False,
        crew_cache_enabled=False,
    )


def make_llm() -> LLM:
    return LLM(
        model="ollama/offline-test",
        base_url="http://localhost:11434",
        api_key="offline-test-key",
        temperature=0.0,
        max_tokens=256,
    )


def test_crew_factory_builds_five_agents_and_six_tasks() -> None:
    factory = TravelCrewFactory(
        llm=make_llm(),
        settings=make_settings(),
    )

    crew = factory.build()

    assert isinstance(crew, Crew)
    assert len(factory.agents) == 5
    assert len(factory.tasks) == 6
    assert len(crew.agents) == 5
    assert len(crew.tasks) == 6


def test_crew_process_is_sequential() -> None:
    crew = TravelCrewFactory(
        llm=make_llm(),
        settings=make_settings(),
    ).build()

    assert crew.process == Process.sequential


def test_factory_does_not_call_kickoff(monkeypatch) -> None:
    kickoff_called = False

    def fail_if_called(*args, **kwargs):
        nonlocal kickoff_called
        kickoff_called = True
        raise AssertionError("Crew kickoff must not run during assembly")

    monkeypatch.setattr(Crew, "kickoff", fail_if_called)

    factory = TravelCrewFactory(
        llm=make_llm(),
        settings=make_settings(),
    )

    crew = factory.build()

    assert isinstance(crew, Crew)
    assert kickoff_called is False


def test_crew_construction_makes_no_http_requests(monkeypatch) -> None:
    import httpx

    def block_request(*args, **kwargs):
        raise AssertionError("Crew construction must not make HTTP requests")

    monkeypatch.setattr(httpx.Client, "get", block_request)
    monkeypatch.setattr(httpx.Client, "post", block_request)

    factory = TravelCrewFactory(
        llm=make_llm(),
        settings=make_settings(),
    )

    crew = factory.build()

    assert isinstance(crew, Crew)


def test_factory_exposes_agent_and_task_collections() -> None:
    factory = TravelCrewFactory(
        llm=make_llm(),
        settings=make_settings(),
    )

    factory.build()

    assert set(factory.agents) == {
        "travel_coordinator",
        "destination_researcher",
        "hotel_transport_specialist",
        "budget_analyst",
        "itinerary_planner",
    }

    assert tuple(factory.tasks) == (
        "requirements_coordination",
        "destination_research",
        "hotel_transport_research",
        "budget_analysis",
        "itinerary_planning",
        "final_coordinator_review",
    )
