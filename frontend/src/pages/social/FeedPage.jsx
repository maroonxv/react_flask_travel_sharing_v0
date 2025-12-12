import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Plus, X, Search } from 'lucide-react';
import { getFeed } from '../../api/social';
import PostCard from '../../components/PostCard';
import Button from '../../components/Button';
import styles from './FeedPage.module.css';

const FeedPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const currentTag = searchParams.get('tag');
    const currentSearch = searchParams.get('search') || '';
    const [tempSearch, setTempSearch] = useState(currentSearch);
    
    // New: Filter Tabs State
    const [activeTab, setActiveTab] = useState('recommend'); // recommend, latest, hot

    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const LIMIT = 10;

    useEffect(() => {
        setTempSearch(currentSearch);
    }, [currentSearch]);

    useEffect(() => {
        const loadInitial = async () => {
            setLoading(true);
            try {
                const tags = currentTag ? [currentTag] : [];
                // Pass activeTab to API if supported later. For now just reloading.
                // potentially: getFeed(LIMIT, 0, tags, currentSearch, activeTab)
                const data = await getFeed(LIMIT, 0, tags, currentSearch);
                const newPosts = Array.isArray(data) ? data : (data.posts || []);
                
                // Client-side simple sort for MVP demo if needed, 
                // but usually better to rely on server. 
                // Let's just use server order for 'recommend' and 'latest'.
                // For 'hot', we could try to sort if we had all data, but with pagination it's tricky.
                // So we just display the data as is, assuming server handles it or will handle it.
                
                setPosts(newPosts);
                setOffset(LIMIT);
                setHasMore(newPosts.length === LIMIT);
            } catch (error) {
                console.error('Failed to fetch feed', error);
            } finally {
                setLoading(false);
            }
        };
        loadInitial();
    }, [currentTag, currentSearch, activeTab]); // Reload when tab changes

    const handleLoadMore = async () => {
        if (loading) return;
        setLoading(true);
        try {
            const tags = currentTag ? [currentTag] : [];
            const data = await getFeed(LIMIT, offset, tags, currentSearch);
            const newPosts = Array.isArray(data) ? data : (data.posts || []);

            setPosts(prev => {
                const existingIds = new Set(prev.map(p => p.id));
                const uniqueNewPosts = newPosts.filter(p => !existingIds.has(p.id));
                return [...prev, ...uniqueNewPosts];
            });
            setOffset(prev => prev + LIMIT);
            setHasMore(newPosts.length === LIMIT);
        } catch (error) {
            console.error('Failed to fetch more posts', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        setSearchParams(prev => {
            const newParams = new URLSearchParams(prev);
            if (tempSearch) newParams.set('search', tempSearch);
            else newParams.delete('search');
            return newParams;
        });
    };

    const clearTag = () => {
        setSearchParams(prev => {
            const newParams = new URLSearchParams(prev);
            newParams.delete('tag');
            return newParams;
        });
    };

    const renderHeader = () => (
        <div className={styles.header}>
            <div className={styles.topRow}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <h1 className={styles.title}>
                        {currentTag ? `标签: #${currentTag}` : '社区动态'}
                    </h1>
                    {currentTag && (
                        <button onClick={clearTag} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                            <X size={20} />
                        </button>
                    )}
                </div>
                <Link to="/social/create">
                    <Button variant="social">
                        <Plus size={18} style={{ marginRight: '0.5rem' }} />
                        发布
                    </Button>
                </Link>
            </div>

            <div className={styles.searchRow}>
                <form onSubmit={handleSearch} className={styles.searchForm}>
                    <Search size={16} className={styles.searchIcon} />
                    <input 
                        type="text"
                        value={tempSearch}
                        onChange={(e) => setTempSearch(e.target.value)}
                        placeholder="搜索帖子..."
                        className={styles.searchInput}
                    />
                </form>
            </div>

            {!currentTag && !currentSearch && (
                <div className={styles.filterTabs}>
                    <button 
                        className={`${styles.filterTab} ${activeTab === 'recommend' ? styles.activeTab : ''}`}
                        onClick={() => setActiveTab('recommend')}
                    >
                        推荐
                    </button>
                    <button 
                        className={`${styles.filterTab} ${activeTab === 'latest' ? styles.activeTab : ''}`}
                        onClick={() => setActiveTab('latest')}
                    >
                        最新
                    </button>
                    <button 
                        className={`${styles.filterTab} ${activeTab === 'hot' ? styles.activeTab : ''}`}
                        onClick={() => setActiveTab('hot')}
                    >
                        热门
                    </button>
                </div>
            )}
        </div>
    );

    return (
        <div className={styles.container}>
            {renderHeader()}

            <div className={styles.feed}>
                {posts.map(post => (
                    <PostCard key={post.id} post={post} />
                ))}
            </div>

            {loading && <div className={styles.loading}>加载中...</div>}

            {!loading && hasMore && (
                <div className={styles.loadMore}>
                    <Button variant="secondary" onClick={handleLoadMore}>
                        加载更多
                    </Button>
                </div>
            )}

            {!loading && !hasMore && posts.length > 0 && (
                <div className={styles.endMessage}>到底啦！</div>
            )}

            {!loading && posts.length === 0 && (
                <div className={styles.endMessage}>
                    {currentTag ? '该标签下暂无帖子' : '还没有帖子，快来抢沙发！'}
                </div>
            )}
        </div>
    );
};

export default FeedPage;
