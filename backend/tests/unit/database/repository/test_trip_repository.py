import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
from unittest.mock import Mock, MagicMock

from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl
from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.value_objects.travel_value_objects import TripId, TripName, TripDescription, DateRange, Money, TripVisibility
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO, TripDayPO
from datetime import date

class TestTripRepository:
    
    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return TripRepositoryImpl(mock_dao)

    @pytest.fixture
    def trip(self):
        return Trip.create(
            name=TripName("Trip"),
            description=TripDescription("Desc"),
            creator_id="u1",
            date_range=DateRange(date(2023,1,1), date(2023,1,3)),
            budget=Money(100, "USD"),
            visibility=TripVisibility.PUBLIC
        )

    def test_save_new_trip(self, repo, mock_dao, trip):
        mock_dao.find_by_id.return_value = None
        
        repo.save(trip)
        
        mock_dao.add.assert_called_once()
        args, _ = mock_dao.add.call_args
        assert isinstance(args[0], TripPO)
        assert args[0].id == trip.id.value

    def test_save_existing_trip(self, repo, mock_dao, trip):
        existing_po = Mock(spec=TripPO)
        existing_po.members = []
        # Use a real list for days to support clear() and append()
        existing_po.days = [] 
        mock_dao.find_by_id.return_value = existing_po
        
        repo.save(trip)
        
        existing_po.update_from_domain.assert_called_once_with(trip)
        mock_dao.update.assert_called_once_with(existing_po)
        
        # Verify days were cleared and re-added
        # Since we used a real list, we check its content
        assert len(existing_po.days) == 3 # Trip fixture has 3 days

    def test_find_by_id(self, repo, mock_dao):
        po = Mock(spec=TripPO)
        expected_domain = Mock(spec=Trip)
        po.to_domain.return_value = expected_domain
        mock_dao.find_by_id.return_value = po
        
        result = repo.find_by_id(TripId("t1"))
        assert result == expected_domain

    def test_find_by_member(self, repo, mock_dao):
        po = Mock(spec=TripPO)
        po.to_domain.return_value = "trip"
        mock_dao.find_by_member.return_value = [po]
        
        result = repo.find_by_member("u1")
        assert result == ["trip"]

    def test_find_public(self, repo, mock_dao):
        po = Mock(spec=TripPO)
        po.to_domain.return_value = "trip"
        mock_dao.find_public.return_value = [po]
        
        result = repo.find_public(limit=10, offset=5)
        assert result == ["trip"]
        mock_dao.find_public.assert_called_with(10, 5)

    def test_delete(self, repo, mock_dao):
        repo.delete(TripId("t1"))
        mock_dao.delete.assert_called_with("t1")

    def test_exists(self, repo, mock_dao):
        mock_dao.exists.return_value = True
        assert repo.exists(TripId("t1")) is True
