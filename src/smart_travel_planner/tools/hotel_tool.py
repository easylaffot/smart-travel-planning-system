"""CrewAI hotel-search tool."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from smart_travel_planner.providers import MockTravelProvider


class HotelSearchInput(BaseModel):
    """Validated arguments for hotel searches."""

    destination: str = Field(min_length=2)
    nights: int = Field(ge=1, le=30)
    travellers: int = Field(ge=1, le=20)
    preference: str = Field(default="mid_range")
    currency: str = Field(default="INR", min_length=3, max_length=3)


class HotelSearchTool(BaseTool):
    """Search mock hotel inventory during the prototype phase."""

    name: str = "hotel_search"
    description: str = (
        "Find accommodation options and calculate room totals. "
        "Results are prototype mock data and are clearly marked as mock."
    )
    args_schema: type[BaseModel] = HotelSearchInput

    def _run(
        self,
        destination: str,
        nights: int,
        travellers: int,
        preference: str = "mid_range",
        currency: str = "INR",
    ) -> str:
        provider = MockTravelProvider()
        options = provider.find_hotels(
            destination=destination,
            nights=nights,
            travellers=travellers,
            preference=preference,
            currency=currency,
        )

        return HotelSearchResult(
            status="success",
            data_mode="mock",
            warning="Prototype prices are not live booking offers.",
            options=[option.model_dump(mode="json") for option in options],
        ).model_dump_json(indent=2)


class HotelSearchResult(BaseModel):
    """Structured hotel tool response."""

    status: str
    data_mode: str
    warning: str
    options: list[dict]
