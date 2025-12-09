import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
from datetime import datetime
import uuid
from typing import List

from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.value_objects.social_value_objects import (
    PostId, PostContent, PostVisibility
)
from app_social.domain.entity.comment_entity import Comment
from app_social.domain.entity.like_entity import Like
from app_social.domain.domain_event.social_events import (
    PostCreatedEvent, PostUpdatedEvent, PostDeletedEvent,
    PostVisibilityChangedEvent, CommentAddedEvent, CommentRemovedEvent,
    PostLikedEvent, PostUnlikedEvent, PostSharedEvent
)

class TestPostAggregate:
    
    @pytest.fixture
    def author_id(self):
        return "user_1"
        
    @pytest.fixture
    def post_content(self):
        return PostContent(title="Test Title", text="Test Text", images=(), tags=())

    @pytest.fixture
    def post(self, author_id, post_content):
        return Post.create(author_id, post_content)

    def test_create_post(self, author_id, post_content):
        post = Post.create(author_id, post_content)
        
        assert post.id is not None
        assert post.author_id == author_id
        assert post.content == post_content
        assert post.visibility == PostVisibility.PUBLIC
        assert post.trip_id is None
        assert not post.is_deleted
        assert post.created_at is not None
        assert post.updated_at is not None
        
        events = post.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], PostCreatedEvent)
        assert events[0].post_id == post.id.value
        assert events[0].author_id == author_id

    def test_create_travel_log(self, author_id, post_content):
        trip_id = "trip_1"
        post = Post.create_travel_log(author_id, trip_id, post_content)
        
        assert post.trip_id == trip_id
        assert post.is_travel_log
        assert post.visibility == PostVisibility.PUBLIC

    def test_reconstitute(self, author_id, post_content):
        post_id = PostId.generate()
        created_at = datetime.utcnow()
        updated_at = datetime.utcnow()
        comments = []
        likes = []
        
        post = Post.reconstitute(
            post_id=post_id,
            author_id=author_id,
            content=post_content,
            comments=comments,
            likes=likes,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert post.id == post_id
        assert post.author_id == author_id
        assert post.created_at == created_at
        assert post.updated_at == updated_at

    def test_update_content(self, post):
        new_content = PostContent(title="New Title", text="New Text")
        post.update_content(new_content)
        
        assert post.content == new_content
        assert post.updated_at > post.created_at
        
        events = post.pop_events()
        # Expecting PostCreatedEvent (from fixture) and PostUpdatedEvent
        # Wait, fixture creates post, which adds event. 
        # But we didn't clear events in fixture. 
        # Let's check if pop_events clears all. Yes.
        # But fixture returns post, and create() adds event.
        # So events list has [PostCreatedEvent, PostUpdatedEvent]
        assert len(events) == 2
        assert isinstance(events[1], PostUpdatedEvent)

    def test_update_content_deleted(self, post):
        post.soft_delete()
        new_content = PostContent(title="New Title", text="New Text")
        with pytest.raises(ValueError, match="Cannot update deleted post"):
            post.update_content(new_content)

    def test_change_visibility(self, post):
        post.change_visibility(PostVisibility.PRIVATE)
        assert post.visibility == PostVisibility.PRIVATE
        
        events = post.pop_events()
        assert len(events) == 2
        assert isinstance(events[1], PostVisibilityChangedEvent)
        
        # Change to same visibility - no event
        post.change_visibility(PostVisibility.PRIVATE)
        assert len(post.pop_events()) == 0

    def test_change_visibility_deleted(self, post):
        post.soft_delete()
        with pytest.raises(ValueError, match="Cannot change visibility of deleted post"):
            post.change_visibility(PostVisibility.PRIVATE)

    def test_soft_delete(self, post):
        post.soft_delete()
        assert post.is_deleted
        
        events = post.pop_events()
        assert isinstance(events[1], PostDeletedEvent)
        
        # Delete again - idempotent
        post.soft_delete()
        assert len(post.pop_events()) == 0

    def test_add_comment(self, post):
        comment = post.add_comment("user_2", "Nice post!")
        
        assert len(post.comments) == 1
        assert post.comment_count == 1
        assert comment.content == "Nice post!"
        
        events = post.pop_events()
        assert isinstance(events[1], CommentAddedEvent)

    def test_add_reply_comment(self, post):
        parent = post.add_comment("user_2", "Parent")
        reply = post.add_comment("user_3", "Reply", parent_comment_id=parent.comment_id)
        
        assert reply.parent_id == parent.comment_id
        
        events = post.pop_events()
        # 0: created, 1: parent added, 2: reply added
        assert isinstance(events[2], CommentAddedEvent)
        assert events[2].parent_comment_id == parent.comment_id

    def test_add_comment_deleted_post(self, post):
        post.soft_delete()
        with pytest.raises(ValueError, match="Cannot comment on deleted post"):
            post.add_comment("user_2", "text")

    def test_add_reply_to_nonexistent_parent(self, post):
        with pytest.raises(ValueError, match="Parent comment not found or deleted"):
            post.add_comment("user_2", "text", parent_comment_id="fake_id")

    def test_remove_comment(self, post):
        comment = post.add_comment("user_2", "text")
        post.remove_comment(comment.comment_id, "user_2")
        
        assert len(post.comments) == 0 # comments property filters deleted
        assert post.comment_count == 0
        
        events = post.pop_events()
        assert isinstance(events[2], CommentRemovedEvent)

    def test_remove_comment_permission(self, post):
        comment = post.add_comment("user_2", "text")
        
        # Post author can delete
        post.remove_comment(comment.comment_id, post.author_id)
        assert post.comment_count == 0

    def test_remove_comment_unauthorized(self, post):
        comment = post.add_comment("user_2", "text")
        
        with pytest.raises(ValueError, match="Not authorized"):
            post.remove_comment(comment.comment_id, "user_3")

    def test_remove_nonexistent_comment(self, post):
        with pytest.raises(ValueError, match="Comment not found"):
            post.remove_comment("fake_id", "user_1")

    def test_like_unlike(self, post):
        assert post.like("user_2") is True
        assert post.like_count == 1
        assert post.is_liked_by("user_2")
        
        events = post.pop_events()
        assert isinstance(events[1], PostLikedEvent)
        
        # Like again
        assert post.like("user_2") is False
        assert post.like_count == 1
        
        # Unlike
        assert post.unlike("user_2") is True
        assert post.like_count == 0
        assert not post.is_liked_by("user_2")
        
        events = post.pop_events()
        # 0: created, 1: liked, 2: unliked (wait, like again didn't add event)
        # previous pop_events cleared created and liked.
        # so now events has [PostUnlikedEvent]
        assert isinstance(events[0], PostUnlikedEvent)
        
        # Unlike again
        assert post.unlike("user_2") is False

    def test_like_deleted_post(self, post):
        post.soft_delete()
        with pytest.raises(ValueError, match="Cannot like deleted post"):
            post.like("user_2")

    def test_share_to(self, post):
        post.share_to("user_2", ["user_3", "user_4"])
        
        events = post.pop_events()
        assert isinstance(events[1], PostSharedEvent)
        assert events[1].sharer_id == "user_2"
        assert len(events[1].shared_to_ids) == 2

    def test_share_deleted_post(self, post):
        post.soft_delete()
        with pytest.raises(ValueError, match="Cannot share deleted post"):
            post.share_to("user_2", ["user_3"])

    def test_share_no_recipients(self, post):
        with pytest.raises(ValueError, match="Must specify at least one recipient"):
            post.share_to("user_2", [])

    def test_can_be_viewed_by(self, post, author_id):
        assert post.can_be_viewed_by(author_id)
        assert post.can_be_viewed_by("other_user") # Public
        
        post.change_visibility(PostVisibility.PRIVATE)
        assert post.can_be_viewed_by(author_id)
        assert not post.can_be_viewed_by("other_user")
        
        post.change_visibility(PostVisibility.FRIENDS)
        assert post.can_be_viewed_by(author_id)
        assert not post.can_be_viewed_by("other_user", is_friend=False)
        assert post.can_be_viewed_by("friend_user", is_friend=True)
        
        post.soft_delete()
        assert not post.can_be_viewed_by(author_id)

    def test_can_be_edited_by(self, post, author_id):
        assert post.can_be_edited_by(author_id)
        assert not post.can_be_edited_by("other_user")
        
        post.soft_delete()
        assert not post.can_be_edited_by(author_id)

    def test_equality(self, post):
        assert post == post
        assert post != "string"
        
        other_post = Post.create("u2", post.content)
        assert post != other_post
