
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.database.core import engine, Base, SessionLocal
from app_social.services.social_service import SocialService
from app_social.infrastructure.database.persistent_model.post_po import PostPO
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO
# Import other POs to ensure they are registered
from app_social.infrastructure.database.persistent_model.message_po import MessagePO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    logger.info("Setting up database...")
    Base.metadata.create_all(bind=engine)

def verify_post_flow(service: SocialService):
    logger.info("Verifying Post Flow...")
    
    author_id = "user_1"
    viewer_id = "user_2"
    
    # 1. Create Post
    logger.info("1. Creating Post...")
    post_data = service.create_post(
        author_id=author_id,
        title="My Trip to Paris",
        content="It was amazing!",
        tags=["travel", "paris"],
        visibility="public"
    )
    post_id = post_data["post_id"]
    logger.info(f"   Post created: {post_id}")
    
    # 2. Get Post
    logger.info("2. Getting Post...")
    post = service.get_post_detail(post_id, viewer_id)
    assert post is not None
    assert post["title"] == "My Trip to Paris"
    assert post["like_count"] == 0
    assert post["is_liked"] == False
    logger.info("   Post retrieval verified.")
    
    # 3. Like Post
    logger.info("3. Liking Post...")
    service.like_post(post_id, viewer_id)
    post = service.get_post_detail(post_id, viewer_id)
    assert post["like_count"] == 1
    assert post["is_liked"] == True
    logger.info("   Like verified.")
    
    # 4. Comment on Post
    logger.info("4. Commenting on Post...")
    comment_data = service.add_comment(post_id, viewer_id, "Great post!")
    post = service.get_post_detail(post_id, viewer_id)
    assert post["comment_count"] == 1
    assert post["comments"][0]["content"] == "Great post!"
    logger.info("   Comment verified.")
    
    # 5. Update Post
    logger.info("5. Updating Post...")
    service.update_post(post_id, author_id, content="Updated content")
    post = service.get_post_detail(post_id, viewer_id)
    assert post["content"] == "Updated content"
    logger.info("   Update verified.")
    
    logger.info("Post Flow Verified Successfully!")
    return post_id

def verify_conversation_flow(service: SocialService):
    logger.info("Verifying Conversation Flow...")
    
    user1 = "user_A"
    user2 = "user_B"
    
    # 1. Create Conversation
    logger.info("1. Creating Private Chat...")
    conv_data = service.create_private_chat(user1, user2)
    conv_id = conv_data["conversation_id"]
    logger.info(f"   Conversation created: {conv_id}")
    
    # 2. Send Message
    logger.info("2. Sending Message...")
    msg_data = service.send_message(conv_id, user1, "Hello user B!")
    logger.info(f"   Message sent: {msg_data['message_id']}")
    
    # 3. Get Messages (User 2 reads)
    logger.info("3. Reading Messages...")
    messages = service.get_conversation_messages(conv_id, user2)
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello user B!"
    logger.info("   Messages verified.")
    
    # 4. Check Unread Count (User 2 should have 0 unread now)
    # Note: Logic in service.get_conversation_messages calls mark_as_read
    # So checking via get_user_conversations
    convs = service.get_user_conversations(user2)
    my_conv = next(c for c in convs if c["id"] == conv_id)
    assert my_conv["unread_count"] == 0
    assert my_conv["last_message"]["content"] == "Hello user B!"
    logger.info("   Unread count verified.")
    
    logger.info("Conversation Flow Verified Successfully!")

def main():
    try:
        setup_db()
        service = SocialService()
        
        # Verify Flows
        verify_post_flow(service)
        verify_conversation_flow(service)
        
        logger.info("ALL VERIFICATION PASSED!")
    except Exception as e:
        logger.error(f"Verification Failed: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
