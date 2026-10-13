"""Phase 1 validation demonstration entry point."""

from datetime import date, timedelta
from decimal import Decimal

from pydantic import ValidationError

from smart_travel_planner.config.settings import get_settings
from smart_travel_planner.models import Activity, CustomerTravelRequest
from smart_travel_planner.utils.logging_config import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    tomorrow = date.today() + timedelta(days=1)
    request = CustomerTravelRequest(
        starting_location="Mumbai",
        destination="Jaipur",
        start_date=tomorrow,
        end_date=tomorrow + timedelta(days=3),
        travellers=2,
        total_budget=Decimal("60000.00"),
        currency="INR",
        interests=[Activity.SIGHTSEEING, Activity.SHOPPING, Activity.LOCAL_FOOD],
        transport_preference="flight",
    )
    print(request.model_dump_json(indent=2))


if __name__ == "__main__":
    try:
        main()
    except ValidationError as exc:
        raise SystemExit(f"Invalid travel request: {exc}") from exc
