import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from app_travel.services.travel_service import TravelService
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao
from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl
from app_travel.infrastructure.external_service.gaode_geo_service_impl import GaodeGeoServiceImpl

from app_social.services.social_service import SocialService

class TestSearchIntegration:
    
    @pytest.fixture
    def travel_service(self, db_session):
        trip_dao = SqlAlchemyTripDao(db_session)
        trip_repo = TripRepositoryImpl(trip_dao)
        geo_service = GaodeGeoServiceImpl() 
        return TravelService(trip_repository=trip_repo, geo_service=geo_service)

    def test_trip_search(self, travel_service, db_session):
        """Test Trip Search Functionality"""
        creator_id = f"user_{uuid.uuid4()}"
        
        # Create Public Trips
        trip1 = travel_service.create_trip(
            name="Summer Vacation in Paris",
            description="A lovely trip",
            creator_id=creator_id,
            start_date=date.today(),
            end_date=date.today(),
            visibility="public"
        )
        trip2 = travel_service.create_trip(
            name="Winter Skiing",
            description="Snow and Fun in Alps",
            creator_id=creator_id,
            start_date=date.today(),
            end_date=date.today(),
            visibility="public"
        )
        trip3 = travel_service.create_trip(
            name="Hidden Gem",
            description="Secret place",
            creator_id=creator_id,
            start_date=date.today(),
            end_date=date.today(),
            visibility="private"
        )
        db_session.commit()

        # Search "Paris"
        results = travel_service.list_public_trips(search_query="Paris")
        assert len(results) >= 1
        found_ids = [t.id.value for t in results]
        assert trip1.id.value in found_ids

        # Search "Snow" (in description)
        results = travel_service.list_public_trips(search_query="Snow")
        assert len(results) >= 1
        found_ids = [t.id.value for t in results]
        assert trip2.id.value in found_ids

        # Search "Hidden" (Private trip, should not be found even if matches)
        results = travel_service.list_public_trips(search_query="Hidden")
        # Ensure trip3 is NOT in results
        found_ids = [t.id.value for t in results]
        assert trip3.id.value not in found_ids
        
    def test_post_search(self, db_session):
        """Test Post Search Functionality"""
        service = SocialService()
        
        session_proxy = MagicMock(wraps=db_session)
        session_proxy.close = MagicMock()
        
        # Mock SessionLocal to use our test db_session
        with patch('app_social.services.social_service.SessionLocal', return_value=session_proxy):
             author_id = f"author_{uuid.uuid4()}"
             
             # Post 1
             service.create_post(author_id, "Amazing Sunset", "Saw a great sunset today", visibility="public")
             # Post 2
             service.create_post(author_id, "Morning Coffee", "Best coffee in town", visibility="public")
             # Post 3
             service.create_post(author_id, "Private Diary", "Secret thoughts", visibility="private")
             
             db_session.commit()
             
             # Search "Sunset"
             results = service.get_public_feed(search_query="Sunset")
             assert len(results) >= 1
             assert any(p['title'] == "Amazing Sunset" for p in results)
             
             # Search "Coffee"
             results = service.get_public_feed(search_query="Coffee")
             assert len(results) >= 1
             assert any(p['title'] == "Morning Coffee" for p in results)
             
             # Search "Secret"
             results = service.get_public_feed(search_query="Secret")
             # Ensure Private Diary is NOT in results
             assert not any(p['title'] == "Private Diary" for p in results)
