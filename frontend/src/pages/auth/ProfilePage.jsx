import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import styles from './ProfilePage.module.css';
import Button from '../../components/Button';
import Card from '../../components/Card';
import PostCard from '../../components/PostCard';
import TripCard from '../../components/TripCard';
import { getUserPosts } from '../../api/social';
import { getUserTrips } from '../../api/travel';
import { User, MapPin, Mail, Shield, Settings } from 'lucide-react';

const ProfilePage = () => {
    const { user } = useAuth();
    const [posts, setPosts] = useState([]);
    const [trips, setTrips] = useState([]);

    useEffect(() => {
        if (user?.id) {
            const fetchData = async () => {
                try {
                    const [postsData, tripsData] = await Promise.all([
                        getUserPosts(user.id),
                        getUserTrips(user.id)
                    ]);
                    setPosts(Array.isArray(postsData) ? postsData : (postsData.posts || []));
                    setTrips(tripsData || []);
                } catch (error) {
                    console.error("Failed to fetch user data", error);
                }
            };
            fetchData();
        }
    }, [user]);

    if (!user) return <div>加载中...</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.avatar}>
                    {user.profile?.avatar_url ? (
                        <img src={user.profile.avatar_url} alt={user.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                        user.username?.charAt(0).toUpperCase() || 'U'
                    )}
                </div>
                <div className={styles.userInfo}>
                    <h1>{user.username}</h1>
                    <p className={styles.role}>{user.role}</p>
                </div>
                <div style={{ marginLeft: 'auto' }}>
                    <Link to="/profile/edit">
                        <Button variant="secondary" icon={<Settings size={18} />}>
                            管理个人资料
                        </Button>
                    </Link>
                </div>
            </div>

            <div className={styles.grid} style={{ gridTemplateColumns: '1fr', marginBottom: '2rem' }}>
                <Card title="个人信息" className={styles.infoCard}>
                    <div className={styles.infoRow}>
                        <Mail size={18} />
                        <span>{user.email}</span>
                    </div>
                    <div className={styles.infoRow}>
                        <User size={18} />
                        <span>@{user.username}</span>
                    </div>
                    {user.profile?.location && (
                        <div className={styles.infoRow}>
                            <MapPin size={18} />
                            <span>{user.profile.location}</span>
                        </div>
                    )}
                    <div className={styles.infoRow}>
                        <Shield size={18} />
                        <span>角色: {user.role}</span>
                    </div>
                    {user.profile?.bio && (
                        <div className={styles.bio}>
                            <h3>简介</h3>
                            <p>{user.profile.bio}</p>
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
