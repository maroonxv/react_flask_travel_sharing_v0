import pytest
import uuid
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import shutil
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from io import BytesIO

from app_social.services.social_service import SocialService
from shared.database.core import SessionLocal

@pytest.fixture
def social_service(db_session):
    with patch('app_social.services.social_service.SessionLocal', return_value=db_session):
        service = SocialService()
        # Override upload folder to a test directory
        test_upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_uploads")
        if os.path.exists(test_upload_folder):
            shutil.rmtree(test_upload_folder)
        os.makedirs(test_upload_folder)
        
        service._storage_service.upload_folder = test_upload_folder
        
        yield service
        
        # Cleanup
        if os.path.exists(test_upload_folder):
            shutil.rmtree(test_upload_folder)

class TestSocialServiceIntegration:
    
    def test_create_post_with_images(self, social_service, db_session):
        author_id = str(uuid.uuid4())
        
        # Create dummy file
        dummy_file = FileStorage(
            stream=BytesIO(b"fake image content"),
            filename="test_image.jpg",
            content_type="image/jpeg"
        )
        
        result = social_service.create_post(
            author_id=author_id,
            title="Post with Image",
            content="Check this out",
            media_files=[dummy_file],
            tags=["photo"]
        )
        
        post_id = result["post_id"]
        
        # Verify
        db_session.expire_all()
        post_dto = social_service.get_post_detail(post_id, author_id)
        
        assert len(post_dto["media_urls"]) == 1
        image_url = post_dto["media_urls"][0]
        assert "post_images" in image_url
        assert image_url.endswith(".jpg")
        
        # Check if file exists on disk
        # image_url is relative like /static/uploads/post_images/xxx.jpg
        # We need to map it back to our test folder
        # Our test folder is mounted at service._storage_service.upload_folder
        # The service returns path relative to static/uploads (hardcoded in LocalFileStorageService?)
        # Let's check LocalFileStorageService.save implementation:
        # return f"/static/uploads/{sub_folder}/{unique_filename}"
        
        # But we changed upload_folder in fixture.
        # The file is saved in test_upload_folder/post_images/unique_filename
        
        filename = os.path.basename(image_url)
        expected_path = os.path.join(social_service._storage_service.upload_folder, "post_images", filename)
        assert os.path.exists(expected_path)

    def test_create_post(self, social_service, db_session):
        author_id = str(uuid.uuid4())
        result = social_service.create_post(
            author_id=author_id,
            title="Test Post",
            content="Hello World",
            tags=["travel", "fun"]
        )
        
        assert result["post_id"] is not None
        post_id = result["post_id"]
        
        db_session.expire_all()
        post_dto = social_service.get_post_detail(post_id, author_id)
        assert post_dto is not None
        assert post_dto["title"] == "Test Post"
        assert post_dto["tags"] == ("travel", "fun")

    def test_update_post(self, social_service):
        author_id = str(uuid.uuid4())
        create_res = social_service.create_post(author_id, "Old Title", "Old Content")
        post_id = create_res["post_id"]
        
        social_service.update_post(
            post_id=post_id,
            operator_id=author_id,
            title="New Title",
            content="New Content"
        )
        
        updated = social_service.get_post_detail(post_id)
        assert updated["title"] == "New Title"
        assert updated["content"] == "New Content"

    def test_delete_post(self, social_service):
        author_id = str(uuid.uuid4())
        create_res = social_service.create_post(author_id, "To Delete", "...")
        post_id = create_res["post_id"]
        
        social_service.delete_post(post_id, author_id)
        
        with pytest.raises(ValueError, match="Permission denied"):
            social_service.get_post_detail(post_id, author_id)

    def test_like_post(self, social_service):
        author_id = str(uuid.uuid4())
        liker_id = str(uuid.uuid4())
        create_res = social_service.create_post(author_id, "Like Me", "...")
        post_id = create_res["post_id"]
        
        is_liked = social_service.like_post(post_id, liker_id)
        assert is_liked is True
        
        dto = social_service.get_post_detail(post_id, liker_id)
        assert dto["like_count"] == 1
        assert dto["is_liked"] is True
        
        is_liked = social_service.like_post(post_id, liker_id)
        assert is_liked is False
        
        dto = social_service.get_post_detail(post_id, liker_id)
        assert dto["like_count"] == 0
        assert dto["is_liked"] is False

    def test_comment_post(self, social_service):
        author_id = str(uuid.uuid4())
        commenter_id = str(uuid.uuid4())
        create_res = social_service.create_post(author_id, "Comment Me", "...")
        post_id = create_res["post_id"]
        
        comment_res = social_service.add_comment(post_id, commenter_id, "Nice!")
        
        dto = social_service.get_post_detail(post_id)
        assert dto["comment_count"] == 1
        assert dto["comments"][0]["content"] == "Nice!"
        assert dto["comments"][0]["author_id"] == commenter_id

    def test_public_feed(self, social_service):
        u1 = str(uuid.uuid4())
        social_service.create_post(u1, "P1", "C1", tags=["A"])
        social_service.create_post(u1, "P2", "C2", tags=["B"])
        social_service.create_post(u1, "P3", "C3", tags=["A"])
        social_service.create_post(u1, "P4", "C4", visibility="private")
        
        feed = social_service.get_public_feed(limit=10)
        titles = [p["title"] for p in feed]
        assert "P1" in titles
        assert "P2" in titles
        assert "P3" in titles
        assert "P4" not in titles
        
        feed_a = social_service.get_public_feed(tags=["A"])
        titles_a = [p["title"] for p in feed_a]
        assert "P1" in titles_a
        assert "P3" in titles_a
        assert "P2" not in titles_a

    def test_user_posts(self, social_service):
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid4())
        
        social_service.create_post(u1, "U1 P1", "...", visibility="public")
        social_service.create_post(u1, "U1 P2", "...", visibility="private")
        
        posts_u1 = social_service.get_user_posts(u1, viewer_id=u1)
        assert len(posts_u1) == 2
        
        posts_u2 = social_service.get_user_posts(u1, viewer_id=u2)
        assert len(posts_u2) == 1
        assert posts_u2[0]["title"] == "U1 P1"

    def test_conversation_flow(self, social_service):
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid4())
        
        chat_res = social_service.create_private_chat(u1, u2)
        conv_id = chat_res["conversation_id"]
        
        msg_res = social_service.send_message(conv_id, u1, "Hello")
        
        convs = social_service.get_user_conversations(u1)
        assert len(convs) == 1
        assert convs[0]["last_message"]["content"] == "Hello"
        
        msgs = social_service.get_conversation_messages(conv_id, u1)
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hello"
        
        convs_u2 = social_service.get_user_conversations(u2)
        assert convs_u2[0]["unread_count"] == 1
        
        social_service.get_conversation_messages(conv_id, u2)
        convs_u2_after = social_service.get_user_conversations(u2)
        assert convs_u2_after[0]["unread_count"] == 0
