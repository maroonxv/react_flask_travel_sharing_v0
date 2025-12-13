import sys
import os

# Add backend/src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from app import create_app
from shared.database.core import engine, Base

# Import all POs to ensure they are registered with Base
# Auth
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
# Social
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
from app_social.infrastructure.database.po.friendship_po import FriendshipPO
# Travel
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO, TripDayPO, ActivityPO, TransitPO
# AI
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO, AiMessagePO

def init_db():
    print("Creating all database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Successfully created all tables!")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
