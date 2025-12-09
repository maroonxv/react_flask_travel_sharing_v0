import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from datetime import datetime
from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.entity.comment_entity import Comment
from app_social.domain.value_objects.social_value_objects import PostId, PostContent, PostVisibility
from app_social.infrastructure.database.dao_impl.sqlalchemy_post_dao import SqlAlchemyPostDao
from app_social.infrastructure.database.repository_impl.post_repository_impl import PostRepositoryImpl

class TestPostRepositoryIntegration:
    
    @pytest.fixture
    def post_repo(self, integration_db_session):
        post_dao = SqlAlchemyPostDao(integration_db_session)
        return PostRepositoryImpl(post_dao)

    def test_save_full_aggregate(self, post_repo):
        # Arrange
        post_id = str(uuid.uuid4())
        author_id = str(uuid.uuid4())
        
        content = PostContent(
            title="Integration Post",
            text="Testing with MySQL",
            images=("img1.jpg",),
            tags=("python", "mysql")
        )
        
        post = Post.reconstitute(
            post_id=PostId(post_id),
            author_id=author_id,
            content=content,
            comments=[],
            likes=[],
            visibility=PostVisibility.PUBLIC,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_deleted=False
        )
        
        # Add a comment
        # Use domain method to add comment, which handles creation
        post.add_comment(commenter_id="commenter_1", content="Great post!")

        # Act
        post_repo.save(post)

        # Assert
        found_post = post_repo.find_by_id(PostId(post_id))
        assert found_post is not None
        assert found_post.content.title == "Integration Post"
        assert found_post.content.text == "Testing with MySQL"
        assert len(found_post.comments) == 1
        assert found_post.comments[0].content == "Great post!"
        assert found_post.comments[0].author_id == "commenter_1"
        assert "python" in found_post.content.tags

    def test_find_public_feed(self, post_repo):
        # Arrange
        p1_id = str(uuid.uuid4())
        p1 = Post.reconstitute(
            post_id=PostId(p1_id),
            author_id="u1",
            content=PostContent(title="P1", text="T1", tags=("fun",)),
            comments=[], likes=[], visibility=PostVisibility.PUBLIC,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(), is_deleted=False
        )
        
        p2_id = str(uuid.uuid4())
        p2 = Post.reconstitute(
            post_id=PostId(p2_id),
            author_id="u1",
            content=PostContent(title="P2", text="T2", tags=("work",)),
            comments=[], likes=[], visibility=PostVisibility.PRIVATE,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(), is_deleted=False
        )
        
        post_repo.save(p1)
        post_repo.save(p2)

        # Act
        feed = post_repo.find_public_feed(tags=["fun"])

        # Assert
        # Note: Integration DB might have other data, so we check if p1 is present
        feed_ids = [p.id.value for p in feed]
        assert p1_id in feed_ids
        assert p2_id not in feed_ids
