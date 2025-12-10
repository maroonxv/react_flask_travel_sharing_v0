import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './ProfilePage.module.css';
import Button from '../../components/Button';
import Card from '../../components/Card';
import PostCard from '../../components/PostCard';
import TripCard from '../../components/TripCard';
import { getUserPosts, getUserProfile } from '../../api/social';
import { getUserTrips } from '../../api/travel';
import { User, MapPin, Mail, Shield, Settings } from 'lucide-react';

const ProfilePage = () => {
    const { user: currentUser } = useAuth();
    const { userId } = useParams();
    
    const [viewUser, setViewUser] = useState(null);
    const [posts, setPosts] = useState([]);
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);

    const isOwnProfile = !userId || (currentUser && userId === currentUser.id);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                let targetUser = null;
                const targetUserId = userId || currentUser?.id;

                if (!targetUserId) {
                    setLoading(false);
                    return; 
                }

                if (isOwnProfile) {
                    targetUser = currentUser;
                } else {
                    targetUser = await getUserProfile(userId);
                }
                
                setViewUser(targetUser);

                if (targetUser) {
                    const [postsData, tripsData] = await Promise.all([
                        getUserPosts(targetUser.id),
                        getUserTrips(targetUser.id)
                    ]);
                    setPosts(Array.isArray(postsData) ? postsData : (postsData.posts || []));
                    setTrips(tripsData || []);
                }
            } catch (error) {
                console.error("Failed to fetch user data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [userId, currentUser, isOwnProfile]);

    if (loading) return <div>加载中...</div>;
    if (!viewUser) return <div>用户不存在</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.avatar}>
                    {viewUser.profile?.avatar_url ? (
                        <img src={viewUser.profile.avatar_url} alt={viewUser.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                        viewUser.username?.charAt(0).toUpperCase() || 'U'
                    )}
                </div>
                <div className={styles.userInfo}>
                    <h1>{viewUser.username}</h1>
                    <p className={styles.role}>{viewUser.role}</p>
                </div>
                {isOwnProfile && (
                    <div style={{ marginLeft: 'auto' }}>
                        <Link to="/profile/edit">
                            <Button variant="secondary" icon={<Settings size={18} />}>
                                管理个人资料
                            </Button>
                        </Link>
                    </div>
                )}
            </div>

            <div className={styles.grid} style={{ gridTemplateColumns: '1fr', marginBottom: '2rem' }}>
                <Card title="个人信息" className={styles.infoCard}>
                    {isOwnProfile && (
                        <div className={styles.infoRow}>
                            <Mail size={18} />
                            <span>{viewUser.email}</span>
                        </div>
                    )}
                    <div className={styles.infoRow}>
                        <User size={18} />
                        <span>@{viewUser.username}</span>
                    </div>
                    {viewUser.profile?.location && (
                        <div className={styles.infoRow}>
                            <MapPin size={18} />
                            <span>{viewUser.profile.location}</span>
                        </div>
                    )}
                    <div className={styles.infoRow}>
                        <Shield size={18} />
                        <span>角色: {viewUser.role}</span>
                    </div>
                    {viewUser.profile?.bio && (
                        <div className={styles.bio}>
                            <h3>简介</h3>
                            <p>{viewUser.profile.bio}</p>
                        </div>
                    )}
                </Card>
            </div>

            {posts.length > 0 && (
                <>
                    <h2 className={styles.sectionTitle}>我的动态</h2>
                    <div className={styles.itemsGrid}>
                        {posts.map(post => (
                            <PostCard key={post.id} post={post} />
                        ))}
                    </div>
                </>
            )}

            {trips.length > 0 && (
                <>
                    <h2 className={styles.sectionTitle}>我的旅行</h2>
                    <div className={styles.itemsGrid}>
                        {trips.map(trip => (
                            <TripCard key={trip.id} trip={trip} />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
};

export default ProfilePage;
