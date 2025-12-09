import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app_travel.services.travel_service import TravelService
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao
from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl
from app_travel.infrastructure.external_service.gaode_geo_service_impl import GaodeGeoServiceImpl
from app_travel.domain.value_objects.travel_value_objects import (
    TripStatus, MemberRole, ActivityType, TripVisibility
)
from app_travel.domain.aggregate.trip_aggregate import Trip

class TestTravelServiceIntegration:
    
    @pytest.fixture
    def travel_service(self, db_session):
        # 1. Infrastructure Setup
        trip_dao = SqlAlchemyTripDao(db_session)
        trip_repo = TripRepositoryImpl(trip_dao)
        
        # Real Geo Service (as requested)
        # Using the default key found in the source code or environment
        geo_service = GaodeGeoServiceImpl() 
        
        # 2. Service Initialization
        service = TravelService(
            trip_repository=trip_repo,
            geo_service=geo_service
        )
        return service

    def test_trip_lifecycle_crud(self, travel_service):
        """Test Create, Read, Update, Delete and Status changes"""
        creator_id = f"user_{uuid.uuid4()}"
        
        # --- Create ---
        trip = travel_service.create_trip(
            name="Integration Trip",
            description="Testing with real Geo Service",
            creator_id=creator_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            budget_amount=5000.0,
            visibility="public"
        )
        
        assert trip is not None
        assert trip.id is not None
        assert trip.name.value == "Integration Trip"
        assert trip.status == TripStatus.PLANNING
        
        # --- Read ---
        fetched_trip = travel_service.get_trip(trip.id.value)
        assert fetched_trip is not None
        assert fetched_trip.id == trip.id
        assert fetched_trip.creator_id == creator_id
        
        # --- Update ---
        updated_trip = travel_service.update_trip(
            trip_id=trip.id.value,
            name="Updated Trip Name",
            budget_amount=6000.0
        )
        assert updated_trip.name.value == "Updated Trip Name"
        assert updated_trip.budget.amount == Decimal("6000.0")
        
        # --- Status Changes ---
        # Start
        started_trip = travel_service.start_trip(trip.id.value)
        assert started_trip.status == TripStatus.IN_PROGRESS
        
        # Complete
        completed_trip = travel_service.complete_trip(trip.id.value)
        assert completed_trip.status == TripStatus.COMPLETED
        
        # Cancel (should fail from completed? usually yes, but let's try resetting or creating new)
        # Let's create another trip for cancel
        trip2 = travel_service.create_trip(
            name="To Cancel", description="desc", creator_id=creator_id,
            start_date=date.today(), end_date=date.today()
        )
        cancelled_trip = travel_service.cancel_trip(trip2.id.value, reason="Rain")
        assert cancelled_trip.status == TripStatus.CANCELLED
        
        # --- Delete ---
        # Usually can only delete if created by user or admin, service handles repo delete
        result = travel_service.delete_trip(trip2.id.value)
        assert result is True
        assert travel_service.get_trip(trip2.id.value) is None

    def test_member_management(self, travel_service):
        """Test adding, removing, and changing roles of members"""
        creator_id = f"owner_{uuid.uuid4()}"
        trip = travel_service.create_trip(
            name="Team Trip", description="desc", creator_id=creator_id,
            start_date=date.today(), end_date=date.today()
        )
        
        member_id = f"member_{uuid.uuid4()}"
        
        # Add Member
        updated_trip = travel_service.add_member(
            trip_id=trip.id.value,
            user_id=member_id,
            role="member",
            added_by=creator_id
        )
        assert len(updated_trip.members) == 2 # Creator + New Member
        member = next(m for m in updated_trip.members if m.user_id == member_id)
        assert member.role == MemberRole.MEMBER
        
        # Change Role
        updated_trip = travel_service.change_member_role(
            trip_id=trip.id.value,
            user_id=member_id,
            new_role="admin",
            changed_by=creator_id
        )
        member = next(m for m in updated_trip.members if m.user_id == member_id)
        assert member.role == MemberRole.ADMIN
        
        # Remove Member
        updated_trip = travel_service.remove_member(
            trip_id=trip.id.value,
            user_id=member_id,
            removed_by=creator_id
        )
        assert len(updated_trip.members) == 1
        assert not any(m.user_id == member_id for m in updated_trip.members)

    def test_listing_trips(self, travel_service):
        """Test various list methods"""
        user_id = f"u_{uuid.uuid4()}"
        
        # Create 3 trips
        # 1. Created by user, Private
        t1 = travel_service.create_trip(
            name="T1", description="", creator_id=user_id,
            start_date=date.today(), end_date=date.today(), visibility="private"
        )
        # 2. Created by user, Public
        t2 = travel_service.create_trip(
            name="T2", description="", creator_id=user_id,
            start_date=date.today(), end_date=date.today(), visibility="public"
        )
        # 3. Created by other, Public
        t3 = travel_service.create_trip(
            name="T3", description="", creator_id="other",
            start_date=date.today(), end_date=date.today(), visibility="public"
        )
        
        # List User Trips (Member/Creator)
        user_trips = travel_service.list_user_trips(user_id)
        user_trip_ids = [t.id.value for t in user_trips]
        assert t1.id.value in user_trip_ids
        assert t2.id.value in user_trip_ids
        assert t3.id.value not in user_trip_ids
        
        # List Created Trips
        created_trips = travel_service.list_created_trips(user_id)
        created_ids = [t.id.value for t in created_trips]
        assert t1.id.value in created_ids
        assert t2.id.value in created_ids
        assert len(created_trips) == 2
        
        # List Public Trips
        public_trips = travel_service.list_public_trips()
        public_ids = [t.id.value for t in public_trips]
        assert t1.id.value not in public_ids # Private
        assert t2.id.value in public_ids
        assert t3.id.value in public_ids

    def test_activity_management_with_real_geo(self, travel_service):
        """
        Test adding activities with real Geo Service.
        This verifies the integration between TravelService -> Trip -> ItineraryService -> GaodeGeoServiceImpl.
        """
        trip = travel_service.create_trip(
            name="Beijing Tour", description="Real Geo Test", creator_id="u1",
            start_date=date.today(), end_date=date.today()
        )
        
        # 1. Add first activity: Tiananmen Square
        # Using real coordinates helps, but name lookup should also work if logic allows
        # The code uses coordinates if provided, else geocodes name.
        # Let's provide name only to force Geocoding!
        
        res1 = travel_service.add_activity(
            trip_id=trip.id.value,
            day_index=0,
            name="Visit Tiananmen",
            activity_type="sightseeing",
            location_name="北京市天安门广场", # Specific enough for Geocoding
            start_time=time(9, 0),
            end_time=time(11, 0),
            notes="Must see"
        )
        
        trip = travel_service.get_trip(trip.id.value)
        act1 = trip.days[0].activities[0]
        assert act1.location.name == "北京市天安门广场"
        # Since we used real Geo Service, it might have been geocoded inside if the logic supports it
        # Checking `TravelService.add_activity` -> `Trip.add_activity` -> `ItineraryService.calculate_transit`
        # `ItineraryService` might geocode if coordinates are missing.
        # However, `TravelService` creates `Location` with None coords if not provided.
        # Let's check if `act1` has coordinates now.
        # Note: `Trip.add_activity` logic might not update the activity's location in place with geocoded result 
        # unless `ItineraryService` explicitly returns it or `Trip` updates it.
        # But `calculate_distance` in GeoService does geocode if needed.
        
        # 2. Add second activity: Forbidden City (Close to Tiananmen)
        # Let's provide approximate coordinates to test distance calc
        # Forbidden City: 39.916, 116.397
        res2 = travel_service.add_activity(
            trip_id=trip.id.value,
            day_index=0,
            name="Forbidden City",
            activity_type="sightseeing",
            location_name="故宫博物院",
            latitude=39.916345,
            longitude=116.397155,
            start_time=time(13, 0),
            end_time=time(17, 0)
        )
        
        # Verify Transit Calculation
        # res2 is TransitCalculationResult
        # It should contain transit info between Act1 and Act2
        assert res2 is not None
        # There should be a transit added to the trip
        trip = travel_service.get_trip(trip.id.value)
        day0 = trip.days[0]
        assert len(day0.transits) == 1
        transit = day0.transits[0]
        
        # Verify Distance (Should be small, < 2km)
        # Real distance is about 1km walking
        assert transit.route_info.distance_meters > 0
        assert transit.route_info.distance_meters < 5000 # meters
        assert transit.route_info.duration_seconds > 0
        
        # 3. Modify Activity
        # Move Forbidden City to Summer Palace (Yiheyuan) - Farther away
        # Summer Palace: ~39.99, 116.27
        res_mod = travel_service.modify_activity(
            trip_id=trip.id.value,
            day_index=0,
            activity_id=day0.activities[1].id,
            location_name="颐和园",
            latitude=39.9999,
            longitude=116.2755
        )
        
        trip = travel_service.get_trip(trip.id.value)
        new_transit = trip.days[0].transits[0]
        # Distance should increase significantly (> 10km)
        assert new_transit.route_info.distance_meters > 10000 
        
        # 4. Remove Activity
        travel_service.remove_activity(
            trip_id=trip.id.value,
            day_index=0,
            activity_id=day0.activities[1].id
        )
        trip = travel_service.get_trip(trip.id.value)
        assert len(trip.days[0].activities) == 1
        assert len(trip.days[0].transits) == 0

    def test_update_day_itinerary_batch(self, travel_service):
        """Test batch update of itinerary"""
        trip = travel_service.create_trip(
            name="Batch Trip", description="", creator_id="u1",
            start_date=date.today(), end_date=date.today()
        )
        
        activities_data = [
            {
                "name": "Spot A",
                "activity_type": "sightseeing",
                "location_name": "Loc A",
                "latitude": 40.0,
                "longitude": 116.0,
                "start_time": time(9, 0),
                "end_time": time(10, 0)
            },
            {
                "name": "Spot B",
                "activity_type": "dining",
                "location_name": "Loc B",
                "latitude": 40.01, # nearby
                "longitude": 116.01,
                "start_time": time(11, 0),
                "end_time": time(12, 0)
            }
        ]
        
        travel_service.update_day_itinerary(trip.id.value, 0, activities_data)
        
        trip = travel_service.get_trip(trip.id.value)
        assert len(trip.days[0].activities) == 2
        assert len(trip.days[0].transits) == 1
        
    def test_geocode_proxy(self, travel_service):
        """Test the geocode_location proxy method"""
        # Real API call
        result = travel_service.geocode_location("清华大学")
        assert result is not None
        assert result['name'] == "清华大学"
        assert result['latitude'] is not None
        assert result['longitude'] is not None
        assert "北京" in result['address']

    def test_day_attributes(self, travel_service):
        """Test updating day notes and theme"""
        trip = travel_service.create_trip(
            name="Attr Trip", description="", creator_id="u1",
            start_date=date.today(), end_date=date.today()
        )
        
        travel_service.update_day_notes(trip.id.value, 0, "Bring umbrella")
        travel_service.update_day_theme(trip.id.value, 0, "Culture Day")
        
        trip = travel_service.get_trip(trip.id.value)
        day = trip.days[0]
        assert "umbrella" in day.notes
        assert day.theme == "Culture Day"

    def test_trip_statistics(self, travel_service):
        """Test statistics generation"""
        trip = travel_service.create_trip(
            name="Stats Trip", description="", creator_id="u1",
            start_date=date.today(), end_date=date.today()
        )
        
        # Add cost activity
        travel_service.add_activity(
            trip_id=trip.id.value,
            day_index=0,
            name="Expensive Dinner",
            activity_type="dining",
            location_name="Restaurant",
            start_time=time(18, 0),
            end_time=time(20, 0),
            cost_amount=500.0
        )
        
        stats = travel_service.get_trip_statistics(trip.id.value)
        assert stats is not None
        assert stats['total_estimated_cost'] == "CNY 500.00"
        assert stats['activity_count'] == 1
