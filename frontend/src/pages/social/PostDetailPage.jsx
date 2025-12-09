import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPost, addComment, getComments } from '../../api/social';
import PostCard from '../../components/PostCard';
import Input from '../../components/Input';
import Button from '../../components/Button';
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
            // Refresh post/comments
            const postData = await getPost(id); // Simple reload
            setPost(postData);
            if (postData.comments) setComments(postData.comments);
        } catch (error) {
            console.error("Failed to add comment", error);
        }
    };

    if (loading) return <div style={{ padding: '2rem' }}>加载中...</div>;
    if (!post) return <div style={{ padding: '2rem' }}>帖子未找到</div>;

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
                                <div className={styles.commentAvatar}>
                                    {comment.username?.charAt(0).toUpperCase() || 'U'}
                                </div>
                                <div className={styles.commentContent}>
                                    <span className={styles.commentUser}>{comment.username || 'User'}</span>
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
