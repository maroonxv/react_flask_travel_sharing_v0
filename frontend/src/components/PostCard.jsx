import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, MessageCircle, MapPin, Trash2, Share2, Image as ImageIcon, FileText } from 'lucide-react';
import Card from './Card';
import styles from './PostCard.module.css';
import { likePost, deletePost } from '../api/social';
import { useAuth } from '../context/AuthContext';
import ShareModal from '../pages/social/ShareModal';
import { toast } from 'react-hot-toast';

const PostCard = ({ post, onDelete }) => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [likes, setLikes] = useState(post.like_count || 0);
    const [isLiked, setIsLiked] = useState(post.is_liked || false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [showShareModal, setShowShareModal] = useState(false);

    const handleLike = async () => {
        try {
            const data = await likePost(post.id);
            setIsLiked(data.is_liked);
            setLikes(prev => data.is_liked ? prev + 1 : prev - 1);
        } catch (error) {
            console.error("Failed to like post", error);
            toast.error("操作失败");
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("确定要删除这条帖子吗？")) return;
        setIsDeleting(true);
        try {
            await deletePost(post.id);
            toast.success("帖子已删除");
            if (onDelete) {
                onDelete(post.id);
            } else {
                window.location.reload();
            }
        } catch (error) {
            console.error("Failed to delete post", error);
            toast.error("删除失败");
            setIsDeleting(false);
        }
    };

    const handleImageClick = (e) => {
        e.preventDefault();
        // MVP: 点击图片跳转到详情页
        navigate(`/social/post/${post.id}`);
    };

    const renderMediaArea = () => {
        const hasMedia = post.media_urls && post.media_urls.length > 0;

        if (hasMedia) {
            return (
                <div className={styles.mediaArea} onClick={handleImageClick} style={{ cursor: 'pointer' }}>
                    <img src={post.media_urls[0]} alt="Post Cover" className={styles.mediaCover} />
                    {post.media_urls.length > 1 && (
                        <div className={styles.imageBadge}>
                            <ImageIcon size={12} />
                            <span>{post.media_urls.length}</span>
                        </div>
                    )}
                </div>
            );
        } else {
            return (
                <div className={styles.mediaArea}>
                    <div className={styles.placeholder}>
                        <div className={styles.placeholderIcon}>
                            {post.trip ? <MapPin size={32} /> : <FileText size={32} />}
                        </div>
                        <div className={styles.placeholderText}>
                            {post.title || post.content}
                        </div>
                    </div>
                </div>
            );
        }
    };

    return (
        <Card className={styles.postCard}>
            {/* 1. Top: Media Area (Fixed Height) */}
            {renderMediaArea()}

            {/* 2. Header: User Info */}
            <div className={styles.header}>
                <Link to={`/profile/${post.author_id}`} className={styles.userInfo} style={{ textDecoration: 'none', color: 'inherit' }}>
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

            {/* 3. Content: Text */}
            <div className={styles.content}>
                {/* 如果是无图模式且标题已在占位符显示，这里可以隐藏标题，或者保留以保持一致性。这里保留。 */}
                <Link to={`/social/post/${post.id}`} className={styles.titleLink}>
                    <h3 className={styles.title}>{post.title || '无标题帖子'}</h3>
                </Link>
                
                <div className={styles.textContainer}>
                    <p className={`${styles.text} ${!isExpanded ? styles.textCollapsed : ''}`}>
                        {post.content}
                    </p>
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
                            <Link to={`/travel/${post.trip.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
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
                <button className={styles.actionBtn} onClick={() => setShowShareModal(true)}>
                    <Share2 size={18} />
                    <span>分享</span>
                </button>
            </div>
            
            <ShareModal 
                isOpen={showShareModal} 
                onClose={() => setShowShareModal(false)} 
                post={post} 
            />
        </Card>
    );
};

export default PostCard;
