"""CrewAI transport-search tool."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from smart_travel_planner.providers import MockTravelProvider


class TransportSearchInput(BaseModel):
    """Validated arguments for transport searches."""

    origin: str = Field(min_length=2)
    destination: str = Field(min_length=2)
    travellers: int = Field(ge=1, le=20)
    preferred_mode: str = Field(default="flight")
    currency: str = Field(default="INR", min_length=3, max_length=3)


class TransportSearchResult(BaseModel):
    """Structured transport tool response."""

    status: str
    data_mode: str
    warning: str
    options: list[dict]


class TransportSearchTool(BaseTool):
    """Search mock intercity transport inventory."""

    name: str = "transport_search"
    description: str = (
        "Find intercity flight, train, and bus options with prices and "
        "travel durations. Prototype results are marked as mock."
    )
    args_schema: type[BaseModel] = TransportSearchInput

    def _run(
        self,
        origin: str,
        destination: str,
        travellers: int,
        preferred_mode: str = "flight",
        currency: str = "INR",
    ) -> str:
        provider = MockTravelProvider()
        options = provider.find_transport(
            origin=origin,
            destination=destination,
            travellers=travellers,
            preferred_mode=preferred_mode,
            currency=currency,
        )

        return TransportSearchResult(
            status="success",
            data_mode="mock",
            warning="Prototype prices are not live transport offers.",
            options=[option.model_dump(mode="json") for option in options],
        ).model_dump_json(indent=2)
