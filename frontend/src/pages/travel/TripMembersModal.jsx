import { useState } from 'react';
import { Link } from 'react-router-dom';
import { removeMember } from '../../api/travel';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import Modal from '../../components/Modal';
import { Trash2, Shield } from 'lucide-react';
import { toast } from 'react-hot-toast';
import styles from './TripMembersModal.module.css';

const TripMembersModal = ({ trip, onClose, onSuccess, isOpen = true }) => {
    const { user } = useAuth();
    const [loadingId, setLoadingId] = useState(null);
    const [error, setError] = useState('');

    const currentUserMember = trip.members.find(m => m.user_id === user?.id);
    const isCurrentUserAdmin = user?.id === trip.creator_id || currentUserMember?.role === 'admin' || currentUserMember?.role === 'owner';

    const handleRemove = async (memberId) => {
        if (!window.confirm('确定要移除该成员吗？')) return;
        
        setLoadingId(memberId);
        setError('');
        
        try {
            await removeMember(trip.id, memberId);
            toast.success("移除成员成功");
            onSuccess(); // Refresh trip data
        } catch (err) {
            console.error("Failed to remove member", err);
            const errMsg = err.response?.data?.error || "移除成员失败";
            toast.error(errMsg);
            setError(errMsg);
            setLoadingId(null);
        }
    };

    return (
        <Modal
            title={`成员列表 (${trip.members.length})`}
            isOpen={isOpen}
            onClose={onClose}
        >
            {error && <div className={styles.error}>{error}</div>}

            <div className={styles.memberList}>
                {trip.members.map(member => (
                    <div key={member.user_id} className={styles.memberItem}>
                        <Link 
                            to={`/profile/${member.user_id}`}
                            onClick={onClose}
                            className={styles.memberLink}
                        >
                            {/* Avatar */}
                            <div className={styles.avatar}>
                                {member.avatar_url ? (
                                    <img src={member.avatar_url} alt={member.username} className={styles.avatarImg} />
                                ) : (
                                    <span className={styles.avatarInitial}>
                                        {member.username?.charAt(0).toUpperCase() || 'U'}
                                    </span>
                                )}
                            </div>
                            
                            {/* Info */}
                            <div>
                                <div className={styles.nameContainer}>
                                    <span className={styles.nickname}>
                                        {member.nickname || member.username}
                                    </span>
                                    {(member.role === 'owner' || member.role === 'admin') && (
                                        <Shield size={14} color="#f59e0b" fill="#f59e0b" />
                                    )}
                                </div>
                                <span className={styles.username}>
                                    @{member.username}
                                </span>
                            </div>
                        </Link>

                        {/* Actions */}
                        {isCurrentUserAdmin && member.user_id !== user?.id && (
                            <button 
                                onClick={() => handleRemove(member.user_id)}
                                disabled={loadingId === member.user_id}
                                className={styles.removeBtn}
                                title="移除成员"
                            >
                                {loadingId === member.user_id ? '...' : <Trash2 size={18} />}
                            </button>
                        )}
                    </div>
                ))}
            </div>

            <div className={styles.actions}>
                <Button variant="secondary" onClick={onClose}>取消</Button>
            </div>
        </Modal>
    );
};

export default TripMembersModal;
