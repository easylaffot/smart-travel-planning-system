"""Offline tests for the five specialized travel agents."""

from crewai import LLM
from crewai.tools import BaseTool

from smart_travel_planner.agents import TravelAgentFactory
from smart_travel_planner.config.settings import Settings


def make_settings() -> Settings:
    """Create isolated execution settings."""

    return Settings(
        _env_file=None,
        app_env="test",
        crew_verbose=False,
        agent_max_iterations=4,
        agent_max_execution_seconds=120,
        crew_cache_enabled=False,
    )


def make_test_llm() -> LLM:
    """Create an LLM object without sending any request."""

    return LLM(
        model="ollama/test-model",
        base_url="http://localhost:11434",
        api_key="offline-test-key",
        temperature=0.0,
        max_tokens=512,
    )


def tool_names(agent_tools: list[BaseTool]) -> set:
    """Return tool names assigned to an agent."""

    return {tool.name for tool in agent_tools}


def test_factory_creates_exactly_five_agents() -> None:
    factory = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    )

    agents = factory.build()

    assert len(agents) == 5
    assert set(agents) == TravelAgentFactory.EXPECTED_AGENT_KEYS


def test_factory_build_does_not_make_http_requests(monkeypatch) -> None:
    import httpx

    def reject_request(*args, **kwargs):
        raise AssertionError("Agent construction must not make HTTP requests")

    monkeypatch.setattr(httpx.Client, "request", reject_request)
    monkeypatch.setattr(httpx.AsyncClient, "request", reject_request)

    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    assert len(agents) == 5


def test_agent_roles_are_unique() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    roles = [agent.role for agent in agents.values()]

    assert len(roles) == len(set(roles))


def test_coordinator_has_no_external_tools() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    coordinator = agents[TravelAgentFactory.COORDINATOR]

    assert coordinator.tools == []
    assert coordinator.allow_delegation is False


def test_destination_researcher_has_only_research_tools() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    researcher = agents[TravelAgentFactory.DESTINATION_RESEARCHER]

    assert tool_names(researcher.tools) == {
        "destination_search",
        "location_lookup",
        "weather_forecast",
        "route_search",
    }


def test_hotel_transport_specialist_has_expected_tools() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    specialist = agents[TravelAgentFactory.HOTEL_TRANSPORT_SPECIALIST]

    assert tool_names(specialist.tools) == {
        "hotel_search",
        "transport_search",
        "route_search",
    }


def test_budget_analyst_only_has_budget_calculator() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    analyst = agents[TravelAgentFactory.BUDGET_ANALYST]

    assert tool_names(analyst.tools) == {
        "travel_budget_calculator",
    }


def test_itinerary_planner_has_schedule_and_routing_tools() -> None:
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
    ).build()

    planner = agents[TravelAgentFactory.ITINERARY_PLANNER]

    assert tool_names(planner.tools) == {
        "itinerary_schedule_validator",
        "route_search",
    }


def test_agent_limits_come_from_settings() -> None:
    settings = make_settings()
    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=settings,
    ).build()

    for agent in agents.values():
        assert agent.max_iter == 4
        assert agent.max_execution_time == 120
        assert agent.verbose is False
        assert agent.allow_delegation is False


def test_tool_overrides_support_offline_isolation() -> None:
    overrides = {
        TravelAgentFactory.DESTINATION_RESEARCHER: [],
    }

    agents = TravelAgentFactory(
        llm=make_test_llm(),
        settings=make_settings(),
        tool_overrides=overrides,
    ).build()

    researcher = agents[TravelAgentFactory.DESTINATION_RESEARCHER]

    assert researcher.tools == []
