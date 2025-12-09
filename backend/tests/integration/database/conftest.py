import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

from shared.database.core import Base

# Import all POs to ensure tables are registered
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO, TripDayPO, ActivityPO

# Load environment variables (to get DATABASE_URL)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../.env')))

@pytest.fixture(scope="session")
def engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not set in .env, skipping integration tests")
    
    # Use the real MySQL database
    engine = create_engine(database_url)
    return engine

@pytest.fixture(scope="session")
def tables(engine):
    # Ensure tables exist
    # NOTE: In a real CI environment, you might want to create a separate test DB.
    # Here we assume the user has configured a DB they are okay with using.
    # Base.metadata.drop_all(engine) # Optional: Start fresh
    Base.metadata.create_all(engine)
    yield
    # Base.metadata.drop_all(engine) # Optional: Clean up after all tests

@pytest.fixture
def integration_db_session(engine, tables):
    """
    Returns a sqlalchemy session backed by the real database.
    Wraps the test in a transaction and rolls it back at the end.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
