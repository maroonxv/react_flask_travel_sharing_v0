import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from datetime import date, datetime
from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.entity.trip_member import TripMember
from app_travel.domain.entity.trip_day_entity import TripDay
from app_travel.domain.value_objects.travel_value_objects import (
    TripId, TripName, TripDescription, DateRange, TripStatus, TripVisibility, MemberRole
)
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao
from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl

class TestTripRepositoryIntegration:
    
    @pytest.fixture
    def trip_repo(self, integration_db_session):
        trip_dao = SqlAlchemyTripDao(integration_db_session)
        return TripRepositoryImpl(trip_dao)

    def test_save_and_find_full_trip(self, trip_repo):
        # Arrange
        trip_id = str(uuid.uuid4())
        creator_id = str(uuid.uuid4())
        
        # Add day
        day = TripDay(day_number=1, date=date.today(), theme="Day 1")
        # trip.days returns a copy, so append won't work on it.
        # Since we are setting up via reconstitute (simulating existing state) or just testing save,
        # we can modify the internal list or pass it in reconstitute.
        # For this test, let's pass it in reconstitute to be clean.
        
        trip = Trip.reconstitute(
            trip_id=TripId(trip_id),
            name=TripName("Integration Trip"),
            description=TripDescription("Desc"),
            creator_id=creator_id,
            date_range=DateRange(date.today(), date.today()),
            members=[],
            days=[day],
            budget=None,
            visibility=TripVisibility.PUBLIC,
            status=TripStatus.PLANNING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add member
        member_id = creator_id[:36]
        trip.add_member(user_id=member_id, role=MemberRole.ADMIN, nickname="Creator")

        # Act
        trip_repo.save(trip)

        # Assert
        found = trip_repo.find_by_id(TripId(trip_id))
        assert found is not None
        assert found.name.value == "Integration Trip"
        assert len(found.members) == 1
        assert found.members[0].user_id == creator_id
        assert len(found.days) == 1
        assert found.days[0].theme == "Day 1"

    def test_find_by_member_integration(self, trip_repo):
        # Arrange
        t1_id = str(uuid.uuid4())
        user_id = "target_user"
        
        t1 = Trip.reconstitute(
            trip_id=TripId(t1_id),
            name=TripName("User's Trip"),
            description=TripDescription(""),
            creator_id=str(uuid.uuid4())[:36], # Ensure creator_id is within 36 chars
            date_range=DateRange(date.today(), date.today()),
            members=[], days=[], budget=None,
            visibility=TripVisibility.PUBLIC, status=TripStatus.PLANNING,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        t1.add_member(user_id=user_id, role=MemberRole.MEMBER, nickname="Member")
        
        trip_repo.save(t1)
        
        # Act
        trips = trip_repo.find_by_member(user_id)
        
        # Assert
        found_ids = [t.id.value for t in trips]
        assert t1_id in found_ids
