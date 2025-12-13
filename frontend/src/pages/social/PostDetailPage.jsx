import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getPost, addComment, getComments } from '../../api/social';
import PostCard from '../../components/PostCard';
import Input from '../../components/Input';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import { toast } from 'react-hot-toast';
import { Send, ArrowLeft } from 'lucide-react';
import styles from './PostDetailPage.module.css';

const PostDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [post, setPost] = useState(null);
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const postData = await getPost(id);
                setPost(postData);
                // If comments are included in postData, use them.
                // Otherwise fetch separate.
                if (postData.comments) {
                    setComments(postData.comments);
                } else {
                    // Try fetch if not included
                    // const commentData = await getComments(id);
                    // setComments(commentData);
                }
            } catch (error) {
                console.error("Failed to load post", error);
                toast.error("加载帖子失败");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        try {
            await addComment(id, newComment);
            setNewComment('');
            toast.success("评论已发布");
            // Refresh post/comments
            const postData = await getPost(id); // Simple reload
            setPost(postData);
            if (postData.comments) setComments(postData.comments);
        } catch (error) {
            console.error("Failed to add comment", error);
            toast.error("评论失败");
        }
    };

    if (loading) return <div className={styles.loading}><LoadingSpinner size="large" /></div>;
    if (!post) return <div className={styles.notFound}>帖子未找到</div>;

    return (
        <div className={styles.container}>
            <button className={styles.backBtn} onClick={() => navigate(-1)}>
                <ArrowLeft size={16} /> 返回
            </button>

            <PostCard post={post} />

            <div className={styles.commentsSection}>
                <h3 className={styles.commentsTitle}>评论</h3>

                <div className={styles.commentsList}>
                    {comments.length === 0 ? (
                        <p className={styles.noComments}>暂无评论。</p>
                    ) : (
                        comments.map((comment, index) => (
                            <div key={index} className={styles.comment}>
                                <Link to={`/profile/${comment.author_id}`} className={`${styles.commentAvatar} ${styles.commentAvatarLink}`}>
                                    {comment.author_avatar ? (
                                        <img src={comment.author_avatar} alt={comment.author_name} className={styles.avatarImg} />
                                    ) : (
                                        (comment.author_name || 'U').charAt(0).toUpperCase()
                                    )}
                                </Link>
                                <div className={styles.commentContent}>
                                    <Link to={`/profile/${comment.author_id}`} className={styles.commentUserLink}>
                                        {comment.author_name || 'User'}
                                    </Link>
                                    <p className={styles.commentText}>{comment.content}</p>
                                    <span className={styles.commentDate}>{new Date(comment.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <form onSubmit={handleCommentSubmit} className={styles.commentForm}>
                    <Input
                        placeholder="写下你的评论..."
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        className={styles.commentInput}
                    />
                    <Button type="submit" variant="social" className={styles.sendBtn} disabled={!newComment.trim()}>
                        <Send size={18} />
                    </Button>
                </form>
            </div>
        </div>
    );
};

export default PostDetailPage;
