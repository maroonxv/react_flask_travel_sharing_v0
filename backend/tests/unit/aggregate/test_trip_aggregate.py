import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock

from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.value_objects.travel_value_objects import (
    TripId, TripName, TripDescription, DateRange, Money,
    TripStatus, TripVisibility, MemberRole, Location, ActivityType
)
from app_travel.domain.entity.activity import Activity
from app_travel.domain.entity.transit import Transit
from app_travel.domain.value_objects.itinerary_value_objects import (
    TransitCalculationResult, ItineraryWarning
)
from app_travel.domain.value_objects.transit_value_objects import (
    TransportMode, RouteInfo
)
from app_travel.domain.domain_event.travel_events import (
    TripCreatedEvent, TripMemberAddedEvent, ActivityAddedEvent
)

class TestTripAggregate:
    
    @pytest.fixture
    def creator_id(self):
        return "user_1"
    
    @pytest.fixture
    def date_range(self):
        start = date(2023, 1, 1)
        end = date(2023, 1, 3) # 3 days
        return DateRange(start, end)
    
    @pytest.fixture
    def trip(self, creator_id, date_range):
        return Trip.create(
            name=TripName("My Trip"),
            description=TripDescription("Desc"),
            creator_id=creator_id,
            date_range=date_range,
            budget=Money(1000, "USD"),
            visibility=TripVisibility.PRIVATE
        )

    def test_create_trip(self, trip, creator_id, date_range):
        assert trip.id is not None
        assert trip.name.value == "My Trip"
        assert trip.status == TripStatus.PLANNING
        assert trip.total_days == 3
        assert len(trip.days) == 3
        assert trip.member_count == 1
        assert trip.is_admin(creator_id)
        
        events = trip.pop_events()
        assert isinstance(events[0], TripCreatedEvent)

    def test_add_member(self, trip):
        trip.add_member("user_2", MemberRole.MEMBER)
        assert trip.member_count == 2
        assert trip.is_member("user_2")
        assert not trip.is_admin("user_2")
        
        events = trip.pop_events()
        assert isinstance(events[1], TripMemberAddedEvent)

    def test_add_member_duplicate(self, trip):
        with pytest.raises(ValueError, match="already a member"):
            trip.add_member(trip.creator_id)

    def test_remove_member(self, trip):
        trip.add_member("user_2")
        trip.remove_member("user_2", removed_by=trip.creator_id)
        assert trip.member_count == 1
        assert not trip.is_member("user_2")

    def test_remove_member_permission(self, trip):
        trip.add_member("user_2")
        trip.add_member("user_3")
        
        with pytest.raises(ValueError, match="Only admin can remove"):
            trip.remove_member("user_2", removed_by="user_3")

    def test_remove_creator_error(self, trip):
        with pytest.raises(ValueError, match="Cannot remove trip creator"):
            trip.remove_member(trip.creator_id, removed_by=trip.creator_id)

    def test_change_member_role(self, trip):
        trip.add_member("user_2")
        trip.change_member_role("user_2", MemberRole.ADMIN, changed_by=trip.creator_id)
        assert trip.is_admin("user_2")
        
        # Demote
        trip.change_member_role("user_2", MemberRole.MEMBER, changed_by=trip.creator_id)
        assert not trip.is_admin("user_2")

    def test_change_creator_role_error(self, trip):
        with pytest.raises(ValueError, match="Cannot demote trip creator"):
            trip.change_member_role(trip.creator_id, MemberRole.MEMBER, changed_by=trip.creator_id)

    def test_add_activity(self, trip):
        location = Location(name="Place", latitude=0, longitude=0, address="Addr")
        activity = Activity.create(
            name="Sightseeing",
            activity_type=ActivityType.SIGHTSEEING,
            location=location,
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time(),
            cost=Money(10, "USD")
        )
        
        trip.add_activity(day_index=0, activity=activity)
        
        day = trip.days[0]
        assert len(day.activities) == 1
        assert day.activities[0].name == "Sightseeing"
        
        events = trip.pop_events()
        # 0: created, 1: activity added
        assert isinstance(events[1], ActivityAddedEvent)

    def test_add_activity_with_transit(self, trip):
        # Mock ItineraryService
        service = Mock()
        transit = Transit(
            id="t1",
            from_activity_id="a1",
            to_activity_id="a2",
            transport_mode=TransportMode.WALKING,
            route_info=RouteInfo(distance_meters=1000, duration_seconds=1800),
            departure_time=datetime(2023, 1, 1, 12, 0).time(),
            arrival_time=datetime(2023, 1, 1, 12, 30).time()
        )
        service.calculate_transit_between_two_activities.return_value = transit
        service.validate_itinerary_feasibility.return_value = []
        
        # Activity 1
        a1 = Activity.create(
            name="A1",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("A", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time()
        )
        trip.add_activity(0, a1)
        
        # Activity 2
        a2 = Activity.create(
            name="A2",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("B", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 13, 0).time(),
            end_time=datetime(2023, 1, 1, 14, 0).time()
        )
        
        result = trip.add_activity(0, a2, itinerary_service=service)
        
        assert result is not None
        assert len(result.transits) == 1
        assert len(trip.days[0].transits) == 1
        service.calculate_transit_between_two_activities.assert_called_once()

    def test_modify_activity(self, trip):
        a1 = Activity.create(
            name="A1",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("A", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time()
        )
        trip.add_activity(0, a1)
        
        trip.modify_activity(0, a1.id, name="A1 Updated")
        
        day = trip.days[0]
        assert day.activities[0].name == "A1 Updated"

    def test_remove_activity(self, trip):
        a1 = Activity.create(
            name="A1",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("A", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time()
        )
        trip.add_activity(0, a1)
        
        trip.remove_activity(0, a1.id)
        assert len(trip.days[0].activities) == 0

    def test_start_complete_cancel(self, trip):
        trip.start()
        assert trip.status == TripStatus.IN_PROGRESS
        
        trip.complete()
        assert trip.status == TripStatus.COMPLETED
        
        # Cannot cancel completed
        with pytest.raises(ValueError):
            trip.cancel()

    def test_cancel_planning(self, trip):
        trip.cancel("Reason")
        assert trip.status == TripStatus.CANCELLED

    def test_update_info(self, trip):
        trip.update_name(TripName("New Name"))
        assert trip.name.value == "New Name"
        
        trip.update_description(TripDescription("New Desc"))
        assert trip.description.value == "New Desc"
        
        trip.update_visibility(TripVisibility.PUBLIC)
        assert trip.visibility == TripVisibility.PUBLIC
        
        trip.update_budget(Money(2000, "USD"))
        assert trip.budget.amount == 2000

    def test_statistics(self, trip):
        # Add an activity with cost
        a1 = Activity.create(
            name="A1",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("A", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time(),
            cost=Money(100, "USD")
        )
        trip.add_activity(0, a1)
        
        stats = trip.generate_statistics()
        assert stats.activity_count == 1
        assert stats.total_estimated_cost.amount == 100

    def test_budget_check(self, trip):
        # Budget is 1000
        a1 = Activity.create(
            name="A1",
            activity_type=ActivityType.SIGHTSEEING,
            location=Location("A", 0, 0, ""),
            start_time=datetime(2023, 1, 1, 10, 0).time(),
            end_time=datetime(2023, 1, 1, 12, 0).time(),
            cost=Money(1500, "USD")
        )
        trip.add_activity(0, a1)
        
        assert not trip.is_within_budget()
