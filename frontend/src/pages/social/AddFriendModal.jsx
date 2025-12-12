import { useState, useEffect } from 'react';
import { Search, UserPlus, Check, X, User } from 'lucide-react';
import { searchUsers, sendFriendRequest } from '../../api/social';
import Button from '../../components/Button';
import Input from '../../components/Input';
import styles from './AddFriendModal.module.css';

const AddFriendModal = ({ onClose }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sentRequests, setSentRequests] = useState(new Set());

    useEffect(() => {
        const timer = setTimeout(() => {
            if (query.trim()) {
                performSearch();
            } else {
                setResults([]);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [query]);

    const performSearch = async () => {
        setLoading(true);
        try {
            const data = await searchUsers(query);
            setResults(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Search failed", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (userId) => {
        try {
            await sendFriendRequest(userId);
            setSentRequests(prev => new Set(prev).add(userId));
        } catch (error) {
            alert("Failed to send request: " + (error.response?.data?.error || error.message));
        }
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <h3>Add Friend</h3>
                    <button className={styles.closeBtn} onClick={onClose}><X size={20}/></button>
                </div>
                
                <div className={styles.searchBar}>
                    <Search size={18} className={styles.searchIcon} />
                    <Input 
                        placeholder="Search by username..." 
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        autoFocus
                    />
                </div>

                <div className={styles.results}>
                    {loading && <div className={styles.loading}>Searching...</div>}
                    {!loading && results.length === 0 && query && (
                        <div className={styles.empty}>No users found</div>
                    )}
                    {results.map(user => (
                        <div key={user.id} className={styles.userRow}>
                            <div className={styles.userInfo}>
                                {user.profile?.avatar_url ? (
                                    <img src={user.profile.avatar_url} className={styles.avatar} alt="" />
                                ) : (
                                    <div className={styles.avatarPlaceholder}><User size={20}/></div>
                                )}
                                <span className={styles.username}>{user.username}</span>
                            </div>
                            {sentRequests.has(user.id) ? (
                                <span className={styles.sentBadge}><Check size={14} /> Sent</span>
                            ) : (
                                <button className={styles.addBtn} onClick={() => handleAdd(user.id)}>
                                    <UserPlus size={18} />
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default AddFriendModal;
