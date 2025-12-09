import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
from datetime import date, datetime
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao

class TestTripDao:
    
    @pytest.fixture
    def trip_dao(self, db_session):
        return SqlAlchemyTripDao(db_session)

    def test_find_by_member(self, trip_dao, db_session):
        # Trip 1: User is member
        t1 = TripPO(
            id="t1", name="Trip 1", creator_id="creator", 
            start_date=date.today(), end_date=date.today(),
            status="planning"
        )
        m1 = TripMemberPO(trip_id="t1", user_id="u_target", role="member")
        
        # Trip 2: User is not member
        t2 = TripPO(
            id="t2", name="Trip 2", creator_id="creator",
            start_date=date.today(), end_date=date.today()
        )
        m2 = TripMemberPO(trip_id="t2", user_id="u_other", role="member")
        
        # Trip 3: User is admin
        t3 = TripPO(
            id="t3", name="Trip 3", creator_id="creator",
            start_date=date.today(), end_date=date.today(),
            status="completed"
        )
        m3 = TripMemberPO(trip_id="t3", user_id="u_target", role="admin")
        
        db_session.add_all([t1, m1, t2, m2, t3, m3])
        db_session.flush()
        
        # Find all trips for u_target
        trips = trip_dao.find_by_member("u_target")
        assert len(trips) == 2
        ids = {t.id for t in trips}
        assert "t1" in ids
        assert "t3" in ids
        
        # Filter by status
        planning_trips = trip_dao.find_by_member("u_target", status="planning")
        assert len(planning_trips) == 1
        assert planning_trips[0].id == "t1"

    def test_find_by_creator(self, trip_dao, db_session):
        t1 = TripPO(id="c1", name="My Trip", creator_id="me", start_date=date.today(), end_date=date.today())
        t2 = TripPO(id="c2", name="Other Trip", creator_id="other", start_date=date.today(), end_date=date.today())
        
        db_session.add_all([t1, t2])
        db_session.flush()
        
        my_trips = trip_dao.find_by_creator("me")
        assert len(my_trips) == 1
        assert my_trips[0].id == "c1"

    def test_find_public(self, trip_dao, db_session):
        t1 = TripPO(id="pub", name="Pub", creator_id="u", start_date=date.today(), end_date=date.today(), visibility="public")
        t2 = TripPO(id="priv", name="Priv", creator_id="u", start_date=date.today(), end_date=date.today(), visibility="private")
        
        db_session.add_all([t1, t2])
        db_session.flush()
        
        public_trips = trip_dao.find_public()
        assert len(public_trips) == 1
        assert public_trips[0].id == "pub"

    def test_crud(self, trip_dao, db_session):
        t = TripPO(
            id="new_trip", name="New", creator_id="u", 
            start_date=date.today(), end_date=date.today()
        )
        trip_dao.add(t)
        
        assert trip_dao.exists("new_trip") is True
        
        t.name = "Updated Name"
        trip_dao.update(t)
        db_session.refresh(t)
        assert trip_dao.find_by_id("new_trip").name == "Updated Name"
        
        trip_dao.delete("new_trip")
        assert trip_dao.exists("new_trip") is False
