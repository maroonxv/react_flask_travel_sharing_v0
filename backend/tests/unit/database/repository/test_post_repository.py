import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
from unittest.mock import Mock, MagicMock, patch

from app_social.infrastructure.database.repository_impl.post_repository_impl import PostRepositoryImpl
from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.value_objects.social_value_objects import PostId, PostContent, PostVisibility
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO

class TestPostRepository:
    
    @pytest.fixture
    def mock_dao(self):
        return Mock()

    @pytest.fixture
    def repo(self, mock_dao):
        return PostRepositoryImpl(mock_dao)

    @pytest.fixture
    def post(self):
        return Post.create("u1", PostContent("Title", "Text"))

    def test_save_new_post(self, repo, mock_dao, post):
        mock_dao.find_by_id.return_value = None
        
        repo.save(post)
        
        mock_dao.add.assert_called_once()
        args, _ = mock_dao.add.call_args
        assert isinstance(args[0], PostPO)
        assert args[0].id == post.id.value

    def test_save_existing_post(self, repo, mock_dao, post):
        existing_po = Mock(spec=PostPO)
        existing_po.comments = []
        existing_po.likes = []
        mock_dao.find_by_id.return_value = existing_po
        
        repo.save(post)
        
        existing_po.update_from_domain.assert_called_once_with(post)
        mock_dao.update.assert_called_once_with(existing_po)

    def test_sync_comments(self, repo, mock_dao, post):
        # Setup existing PO with one comment
        existing_po = Mock(spec=PostPO)
        c_po = Mock(spec=CommentPO)
        c_po.id = "old_comment"
        # Use a list for comments
        existing_po.comments = [c_po]
        # Also initialize likes to avoid iteration error in _sync_likes
        existing_po.likes = []
        
        mock_dao.find_by_id.return_value = existing_po
        
        # Add new comment to domain post
        new_comment = post.add_comment("u2", "Nice")
        
        repo.save(post)
        
        # Verify: 
        # 1. old_comment should be gone from list (filtered out)
        # 2. new_comment should be in list (appended)
        
        # Check the contents of existing_po.comments
        # Note: CommentPO.from_domain is called.
        
        # Check that list contains new comment's PO (or similar)
        assert len(existing_po.comments) == 1
        assert existing_po.comments[0].id == new_comment.comment_id
        
    def test_sync_likes(self, repo, mock_dao, post):
        existing_po = Mock(spec=PostPO)
        existing_po.likes = []
        existing_po.comments = [] # needed for save
        mock_dao.find_by_id.return_value = existing_po
        
        post.like("u2")
        repo.save(post)
        
        # Verify like was added
        assert len(existing_po.likes) == 1 or existing_po.likes.append.called

    def test_find_by_id(self, repo, mock_dao):
        po = Mock(spec=PostPO)
        expected_domain = Mock(spec=Post)
        po.to_domain.return_value = expected_domain
        mock_dao.find_by_id.return_value = po
        
        result = repo.find_by_id(PostId("p1"))
        assert result == expected_domain

    def test_find_by_author(self, repo, mock_dao):
        po = Mock(spec=PostPO)
        po.to_domain.return_value = "domain_post"
        mock_dao.find_by_author.return_value = [po]
        
        result = repo.find_by_author("u1")
        assert result == ["domain_post"]

    def test_find_public_feed(self, repo, mock_dao):
        po = Mock(spec=PostPO)
        po.to_domain.return_value = "domain_post"
        mock_dao.find_public_feed.return_value = [po]
        
        result = repo.find_public_feed(tags=["A"])
        assert result == ["domain_post"]
        mock_dao.find_public_feed.assert_called_with(limit=20, offset=0, tags=["A"])

    def test_delete(self, repo, mock_dao):
        repo.delete(PostId("p1"))
        mock_dao.delete.assert_called_with("p1")

    def test_exists(self, repo, mock_dao):
        mock_dao.exists.return_value = True
        assert repo.exists(PostId("p1")) is True
