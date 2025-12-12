import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, MessageCircle, MapPin, Trash2 } from 'lucide-react';
import Card from './Card';
import styles from './PostCard.module.css';
import { likePost, deletePost } from '../api/social';
import { useAuth } from '../context/AuthContext';

const PostCard = ({ post, onDelete }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [likes, setLikes] = useState(post.like_count || 0);
    const [isLiked, setIsLiked] = useState(post.is_liked || false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);

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
                window.location.reload();
            }
        } catch (error) {
            console.error("Failed to delete post", error);
            alert("删除失败");
            setIsDeleting(false);
        }
    };

    const handleImageClick = (e, index) => {
        e.preventDefault();
        // MVP: 点击图片跳转到详情页
        navigate(`/social/post/${post.id}`);
    };

    const renderMediaGrid = () => {
        if (!post.media_urls || post.media_urls.length === 0) return null;

        const count = post.media_urls.length;
        let gridClass = styles.grid1;
        let showCount = count;

        if (count === 2) {
            gridClass = styles.grid2;
        } else if (count === 3) {
            gridClass = styles.grid3;
        } else if (count >= 4) {
            gridClass = styles.grid4;
            showCount = 4; // 只显示前4张
        }

        return (
            <div className={`${styles.mediaGrid} ${gridClass}`}>
                {post.media_urls.slice(0, showCount).map((url, index) => (
                    <div 
                        key={index} 
                        className={styles.mediaItem}
                        onClick={(e) => handleImageClick(e, index)}
                    >
                        <img src={url} alt={`Post media ${index + 1}`} className={styles.image} />
                        {count > 4 && index === 3 && (
                            <div className={styles.moreOverlay}>
                                +{count - 4}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        );
    };

    return (
        <Card className={styles.postCard}>
            {/* 1. Header: User Info & Actions */}
            <div className={styles.header}>
                <Link to={`/users/${post.author_id}`} className={styles.userInfo} style={{ textDecoration: 'none', color: 'inherit' }}>
                    <div className={styles.avatar}>
                        {post.author_avatar ? (
                             <img src={post.author_avatar} alt={post.author_name} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                        ) : (
                            post.author_name?.charAt(0).toUpperCase()
                        )}
                    </div>
                    <div>
                        <div className={styles.username}>{post.author_name}</div>
                        <div className={styles.date}>{new Date(post.created_at).toLocaleDateString()}</div>
                    </div>
                </Link>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
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

            {/* 2. Content: Title & Text */}
            <div className={styles.content}>
                <Link to={`/social/post/${post.id}`} className={styles.titleLink}>
                    <h3 className={styles.title}>{post.title || '无标题帖子'}</h3>
                </Link>
                
                <div className={styles.textContainer}>
                    <p className={`${styles.text} ${!isExpanded ? styles.textCollapsed : ''}`}>
                        {post.content}
                    </p>
                    {/* 简单的判断：如果字数很多才显示展开按钮。这里暂时简单处理，或者一直显示如果被截断。
                        由于 CSS line-clamp 很难检测是否溢出，这里用字数做一个近似判断 */}
                    {post.content && post.content.length > 100 && (
                        <button 
                            className={styles.expandBtn}
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? '收起' : '展开全文'}
                        </button>
                    )}
                </div>

                {post.trip && (
                    <div className={styles.tripLink}>
                        <MapPin size={14} />
                        {post.trip.is_public ? (
                            <Link to={`/travel/trips/${post.trip.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                                {post.trip.title}
                            </Link>
                        ) : (
                            <span>{post.trip.title}</span>
                        )}
                    </div>
                )}

                {post.tags && post.tags.length > 0 && (
                    <div className={styles.tags}>
                        {post.tags.map((tag, idx) => (
                            <Link key={idx} to={`/social?tag=${tag}`} className={styles.tag} style={{ textDecoration: 'none' }}>
                                #{tag}
                            </Link>
                        ))}
                    </div>
                )}
            </div>

            {/* 3. Media: Grid Layout */}
            {renderMediaGrid()}

            {/* 4. Footer: Actions */}
            <div className={styles.actions}>
                <button className={styles.actionBtn} onClick={handleLike} style={{ color: isLiked ? '#ef4444' : 'inherit' }}>
                    <Heart size={18} fill={isLiked ? '#ef4444' : 'none'} />
                    <span>{likes || '点赞'}</span>
                </button>
                <Link to={`/social/post/${post.id}`} className={styles.actionBtn}>
                    <MessageCircle size={18} />
                    <span>{post.comment_count || '评论'}</span>
                </Link>
            </div>
        </Card>
    );
};

export default PostCard;
