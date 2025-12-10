import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MessageCircle, MapPin } from 'lucide-react';
import Card from './Card';
import styles from './PostCard.module.css';
import { likePost } from '../api/social';

const PostCard = ({ post }) => {
    const [likes, setLikes] = useState(post.like_count || 0);
    const [isLiked, setIsLiked] = useState(post.is_liked || false);

    const handleLike = async () => {
        try {
            const data = await likePost(post.id);
            setIsLiked(data.is_liked);
            setLikes(prev => data.is_liked ? prev + 1 : prev - 1);
        } catch (error) {
            console.error("Failed to like post", error);
        }
    };

    return (
        <Card className={styles.postCard}>
            <div className={styles.header}>
                <div className={styles.userInfo}>
                    <div className={styles.avatar}>
                        {post.author_avatar ? (
                             <img src={post.author_avatar} alt={post.author_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                            post.author_name?.charAt(0).toUpperCase()
                        )}
                    </div>
                    <span className={styles.username}>{post.author_name}</span>
                </div>
                <span className={styles.date}>{new Date(post.created_at).toLocaleDateString()}</span>
            </div>

            {post.media_urls && post.media_urls.length > 0 && (
                <div className={styles.imageContainer}>
                    <img src={post.media_urls[0]} alt={post.title} className={styles.image} />
                    {post.media_urls.length > 1 && (
                        <div className={styles.imageCount}>
                            +{post.media_urls.length - 1}
                        </div>
                    )}
                </div>
            )}

            <div className={styles.content}>
                <Link to={`/social/post/${post.id}`} className={styles.titleLink}>
                    <h3 className={styles.title}>{post.title || '无标题帖子'}</h3>
                </Link>
                <p className={styles.text}>{post.content}</p>

                {post.trip_id && (
                    <div className={styles.tripLink}>
                        <MapPin size={16} />
                        <span>关联旅行: {post.trip_name || '查看旅行'}</span>
                    </div>
                )}

                {post.tags && post.tags.length > 0 && (
                    <div className={styles.tags}>
                        {post.tags.map((tag, idx) => <span key={idx} className={styles.tag}>#{tag}</span>)}
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
                    <span>{post.comments_count || 0}</span>
                </Link>
            </div>
        </Card>
    );
};

export default PostCard;
