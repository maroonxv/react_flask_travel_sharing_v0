import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app_social.infrastructure.database.persistent_model.post_po import (
    PostPO, CommentPO, LikePO, PostImagePO, PostTagPO
)
from app_social.infrastructure.database.dao_impl.sqlalchemy_post_dao import SqlAlchemyPostDao

class TestPostDao:
    
    @pytest.fixture
    def post_dao(self, db_session):
        return SqlAlchemyPostDao(db_session)

    def _create_post(self, post_id, author_id, visibility="public", is_deleted=False, trip_id=None):
        return PostPO(
            id=post_id,
            author_id=author_id,
            title=f"Title {post_id}",
            text=f"Text {post_id}",
            visibility=visibility,
            is_deleted=is_deleted,
            trip_id=trip_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def test_add_and_find_by_id(self, post_dao, db_session):
        post_id = str(uuid.uuid4())
        post = self._create_post(post_id, "user_1")
        
        # Add relations
        post.comments.append(CommentPO(id=str(uuid.uuid4()), post_id=post_id, author_id="u2", content="c1"))
        post.likes.append(LikePO(user_id="u3", post_id=post_id))
        post.images.append(PostImagePO(image_url="/img/1.jpg", display_order=0))
        post.tags.append(PostTagPO(tag="travel"))
        
        post_dao.add(post)
        db_session.flush() # Manually flush as DAO doesn't do it anymore
        
        # Test find_by_id
        found = post_dao.find_by_id(post_id)
        assert found is not None
        assert found.id == post_id
        assert found.title == f"Title {post_id}"
        assert len(found.comments) == 1
        assert len(found.likes) == 1
        assert len(found.images) == 1
        assert len(found.tags) == 1
        assert found.tags[0].tag == "travel"

    def test_find_by_author(self, post_dao, db_session):
        u1 = "user_author_1"
        p1 = self._create_post(str(uuid.uuid4()), u1)
        p2 = self._create_post(str(uuid.uuid4()), u1, is_deleted=True)
        p3 = self._create_post(str(uuid.uuid4()), "other_user")
        
        db_session.add_all([p1, p2, p3])
        db_session.flush()
        
        # Exclude deleted
        posts = post_dao.find_by_author(u1, include_deleted=False)
        assert len(posts) == 1
        assert posts[0].id == p1.id
        
        # Include deleted
        posts_all = post_dao.find_by_author(u1, include_deleted=True)
        assert len(posts_all) == 2
        
        # Pagination
        p4 = self._create_post(str(uuid.uuid4()), u1)
        db_session.add(p4)
        db_session.flush()
        
        # Assuming created_at order, p4 is newest (if datetime resolution allows, otherwise it's fast)
        # But here we didn't sleep, so timestamps might be equal. Sort order is desc(created_at).
        posts_page = post_dao.find_by_author(u1, limit=1, offset=0)
        assert len(posts_page) == 1

    def test_find_by_trip(self, post_dao, db_session):
        trip_id = "trip_1"
        p1 = self._create_post(str(uuid.uuid4()), "u1", trip_id=trip_id)
        p2 = self._create_post(str(uuid.uuid4()), "u1", trip_id="other_trip")
        
        db_session.add_all([p1, p2])
        db_session.flush()
        
        found = post_dao.find_by_trip(trip_id)
        assert found is not None
        assert found.id == p1.id
        
        # Deleted trip post shouldn't be found
        p1.is_deleted = True
        db_session.flush()
        found_deleted = post_dao.find_by_trip(trip_id)
        assert found_deleted is None

    def test_find_public_feed(self, post_dao, db_session):
        # Public post with tag A
        p1 = self._create_post(str(uuid.uuid4()), "u1", visibility="public")
        p1.tags.append(PostTagPO(tag="A"))
        
        # Public post with tag B
        p2 = self._create_post(str(uuid.uuid4()), "u1", visibility="public")
        p2.tags.append(PostTagPO(tag="B"))
        
        # Private post with tag A
        p3 = self._create_post(str(uuid.uuid4()), "u1", visibility="private")
        p3.tags.append(PostTagPO(tag="A"))
        
        # Public post with no tags
        p4 = self._create_post(str(uuid.uuid4()), "u1", visibility="public")
        
        db_session.add_all([p1, p2, p3, p4])
        db_session.flush()
        
        # All public
        feed = post_dao.find_public_feed()
        # Note: Database might have other posts from other tests if session is not isolated properly,
        # but typically unit tests with db_session fixture roll back. 
        # However, to be safe, we check if our posts are in the result.
        feed_ids = [p.id for p in feed]
        assert p1.id in feed_ids
        assert p2.id in feed_ids
        assert p4.id in feed_ids
        assert p3.id not in feed_ids
        
        # Filter by tag A
        feed_a = post_dao.find_public_feed(tags=["A"])
        feed_a_ids = [p.id for p in feed_a]
        assert p1.id in feed_a_ids
        assert p2.id not in feed_a_ids
        assert p3.id not in feed_a_ids # Private
        
        # Filter by tag A or B
        feed_ab = post_dao.find_public_feed(tags=["A", "B"])
        feed_ab_ids = [p.id for p in feed_ab]
        assert p1.id in feed_ab_ids
        assert p2.id in feed_ab_ids

    def test_find_by_visibility(self, post_dao, db_session):
        p1 = self._create_post(str(uuid.uuid4()), "u1", visibility="friends")
        db_session.add(p1)
        db_session.flush()
        
        posts = post_dao.find_by_visibility("friends")
        assert any(p.id == p1.id for p in posts)

    def test_update(self, post_dao, db_session):
        post = self._create_post(str(uuid.uuid4()), "u1")
        post_dao.add(post)
        db_session.flush()
        
        post.title = "Updated Title"
        post_dao.update(post)
        db_session.flush()
        
        updated = post_dao.find_by_id(post.id)
        assert updated.title == "Updated Title"

    def test_delete(self, post_dao, db_session):
        post = self._create_post(str(uuid.uuid4()), "u1")
        post_dao.add(post)
        db_session.flush()
        
        post_dao.delete(post.id)
        db_session.flush()
        
        assert post_dao.find_by_id(post.id) is None

    def test_exists(self, post_dao, db_session):
        post = self._create_post(str(uuid.uuid4()), "u1")
        post_dao.add(post)
        db_session.flush()
        
        assert post_dao.exists(post.id) is True
        assert post_dao.exists("non_existent_id") is False

    def test_count_by_author(self, post_dao, db_session):
        u1 = str(uuid.uuid4())
        p1 = self._create_post(str(uuid.uuid4()), u1)
        p2 = self._create_post(str(uuid.uuid4()), u1, is_deleted=True)
        
        db_session.add_all([p1, p2])
        db_session.flush()
        
        assert post_dao.count_by_author(u1, include_deleted=False) == 1
        assert post_dao.count_by_author(u1, include_deleted=True) == 2
