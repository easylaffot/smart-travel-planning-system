"""Convert validated customer requests into CrewAI kickoff inputs."""

from smart_travel_planner.models import CustomerTravelRequest


class KickoffInputBuilder:
    """Build stable, JSON-compatible inputs for CrewAI tasks."""

    def build(
        self,
        request: CustomerTravelRequest,
    ) -> dict[str, object]:
        """Return all validated customer requirements."""

        return {
            "starting_location": request.starting_location,
            "destination": request.destination,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "duration_days": request.duration_days,
            "travellers": request.travellers,
            "total_budget": str(request.total_budget),
            "currency": request.currency,
            "interests": [interest.value for interest in request.interests],
            "accommodation_preference": (request.accommodation_preference.value),
            "transport_preference": request.transport_preference,
            "special_requirements": request.special_requirements,
        }
