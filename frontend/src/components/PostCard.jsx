import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MessageCircle, MapPin, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import Card from './Card';
import styles from './PostCard.module.css';
import { likePost, deletePost } from '../api/social';
import { useAuth } from '../context/AuthContext';

const PostCard = ({ post, onDelete }) => {
    const { user } = useAuth();
    const [likes, setLikes] = useState(post.like_count || 0);
    const [isLiked, setIsLiked] = useState(post.is_liked || false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const handleLike = async () => {
        try {
            const data = await likePost(post.id);
            setIsLiked(data.is_liked);
            setLikes(prev => data.is_liked ? prev + 1 : prev - 1);
        } catch (error) {
            console.error("Failed to like post", error);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("确定要删除这条帖子吗？")) return;
        setIsDeleting(true);
        try {
            await deletePost(post.id);
            if (onDelete) {
                onDelete(post.id);
            } else {
                // If no callback, maybe just hide it or reload?
                // Reloading is safe but jarring.
                window.location.reload();
            }
        } catch (error) {
            console.error("Failed to delete post", error);
            alert("删除失败");
            setIsDeleting(false);
        }
    };

    return (
        <Card className={styles.postCard}>
            <div className={styles.header}>
                <Link to={`/users/${post.author_id}`} className={styles.userInfo} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <div className={styles.avatar}>
                        {post.author_avatar ? (
                             <img src={post.author_avatar} alt={post.author_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                            post.author_name?.charAt(0).toUpperCase()
                        )}
                    </div>
                    <span className={styles.username}>{post.author_name}</span>
                </Link>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span className={styles.date}>{new Date(post.created_at).toLocaleDateString()}</span>
                    {user && user.id === post.author_id && (
                        <button 
                            onClick={handleDelete} 
                            disabled={isDeleting}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                            title="删除帖子"
                        >
                            <Trash2 size={16} />
                        </button>
                    )}
                </div>
            </div>

            {post.media_urls && post.media_urls.length > 0 && (
                <div className={styles.imageContainer}>
                    <img 
                        src={post.media_urls[currentImageIndex]} 
                        alt={`${post.title} - ${currentImageIndex + 1}`} 
                        className={styles.image} 
                    />
                    
                    {post.media_urls.length > 1 && (
                        <>
                            <button 
                                className={`${styles.navBtn} ${styles.prevBtn}`}
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setCurrentImageIndex(prev => 
                                        prev === 0 ? post.media_urls.length - 1 : prev - 1
                                    );
                                }}
                            >
                                <ChevronLeft size={20} />
                            </button>
                            <button 
                                className={`${styles.navBtn} ${styles.nextBtn}`}
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setCurrentImageIndex(prev => 
                                        prev === post.media_urls.length - 1 ? 0 : prev + 1
                                    );
                                }}
                            >
                                <ChevronRight size={20} />
                            </button>
                            <div className={styles.indicator}>
                                {currentImageIndex + 1} / {post.media_urls.length}
                            </div>
                        </>
                    )}
                </div>
            )}

            <div className={styles.content}>
                <Link to={`/social/post/${post.id}`} className={styles.titleLink}>
                    <h3 className={styles.title}>{post.title || '无标题帖子'}</h3>
                </Link>
                <p className={styles.text}>{post.content}</p>

                {post.trip && (
                    <div className={styles.tripLink}>
                        <MapPin size={16} />
                        {post.trip.is_public ? (
                            <Link to={`/travel/trips/${post.trip.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                                关联旅行: {post.trip.title}
                            </Link>
                        ) : (
                            <span>关联旅行: {post.trip.title}</span>
                        )}
                    </div>
                )}

                {post.tags && post.tags.length > 0 && (
                    <div className={styles.tags}>
                        {post.tags.map((tag, idx) => (
                            <Link key={idx} to={`/social?tag=${tag}`} className={styles.tag} style={{ textDecoration: 'none', color: '#3b82f6' }}>
                                #{tag}
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            <div className={styles.actions}>
                <button className={styles.actionBtn} onClick={handleLike} style={{ color: isLiked ? '#ef4444' : 'inherit' }}>
                    <Heart size={20} fill={isLiked ? '#ef4444' : 'none'} />
                    <span>{likes}</span>
                </button>
                <Link to={`/social/post/${post.id}`} className={styles.actionBtn}>
                    <MessageCircle size={20} />
                    <span>{post.comment_count || 0}</span>
                </Link>
            </div>
        </Card>
    );
};

export default PostCard;
