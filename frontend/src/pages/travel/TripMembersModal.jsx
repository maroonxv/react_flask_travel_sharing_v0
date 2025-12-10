import { useState } from 'react';
import { removeMember } from '../../api/travel';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Card from '../../components/Card';
import { X, Trash2, User, Shield } from 'lucide-react';
import styles from './TripDetail.module.css';

const TripMembersModal = ({ trip, onClose, onSuccess }) => {
    const { user } = useAuth();
    const [loadingId, setLoadingId] = useState(null);
    const [error, setError] = useState('');

    // Determine if current user is admin/owner
    // Assuming creator is owner/admin. 
    // Also check if current user has 'admin' role in members list if applicable.
    // For simplicity, let's use creator_id or check the member role of current user.
    
    const currentUserMember = trip.members.find(m => m.user_id === user?.id);
    const isCurrentUserAdmin = user?.id === trip.creator_id || currentUserMember?.role === 'admin' || currentUserMember?.role === 'owner';

    const handleRemove = async (memberId) => {
        if (!window.confirm('确定要移除该成员吗？')) return;
        
        setLoadingId(memberId);
        setError('');
        
        try {
            await removeMember(trip.id, memberId);
            onSuccess(); // Refresh trip data
        } catch (err) {
            console.error("Failed to remove member", err);
            setError(err.response?.data?.error || "移除成员失败");
            setLoadingId(null);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <Card className={styles.modalContent} title={`成员列表 (${trip.members.length})`}>
                <button className={styles.closeBtn} onClick={onClose}>
                    <X size={20} />
                </button>
                
                {error && <div style={{ color: 'red', marginBottom: '1rem', padding: '0.5rem', background: 'rgba(255,0,0,0.1)', borderRadius: '4px' }}>{error}</div>}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
                    {trip.members.map(member => (
                        <div key={member.user_id} style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'space-between',
                            padding: '0.75rem',
                            backgroundColor: 'rgba(255, 255, 255, 0.05)',
                            borderRadius: '8px',
                            border: '1px solid var(--border-color)'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                {/* Avatar */}
                                <div style={{ 
                                    width: '40px', 
                                    height: '40px', 
                                    borderRadius: '50%', 
                                    backgroundColor: '#3b82f6', 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    overflow: 'hidden',
                                    flexShrink: 0
                                }}>
                                    {member.avatar_url ? (
                                        <img src={member.avatar_url} alt={member.username} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    ) : (
                                        <span style={{ fontWeight: 'bold', color: 'white' }}>
                                            {member.username?.charAt(0).toUpperCase() || 'U'}
                                        </span>
                                    )}
                                </div>
                                
                                {/* Info */}
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                                            {member.nickname || member.username}
                                        </span>
                                        {(member.role === 'owner' || member.role === 'admin') && (
                                            <Shield size={14} color="#f59e0b" fill="#f59e0b" />
                                        )}
                                    </div>
                                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                        @{member.username}
                                    </span>
                                </div>
                            </div>

                            {/* Actions */}
                            {isCurrentUserAdmin && member.user_id !== user?.id && (
                                <button 
                                    onClick={() => handleRemove(member.user_id)}
                                    disabled={loadingId === member.user_id}
                                    style={{ 
                                        background: 'none', 
                                        border: 'none', 
                                        color: '#ef4444', 
                                        cursor: 'pointer',
                                        padding: '0.5rem',
                                        borderRadius: '4px',
                                        transition: 'background 0.2s'
                                    }}
                                    title="移除成员"
                                >
                                    {loadingId === member.user_id ? '...' : <Trash2 size={18} />}
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            </Card>
        </div>
    );
};

export default TripMembersModal;
