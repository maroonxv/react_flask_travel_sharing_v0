import { useState } from 'react';
import { addMember } from '../../api/travel';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import { X } from 'lucide-react';
import styles from './TripDetail.module.css';

const AddMemberModal = ({ tripId, onClose, onSuccess }) => {
    const [userId, setUserId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            await addMember(tripId, userId);
            onSuccess();
            onClose();
        } catch (err) {
            console.error("Failed to add member", err);
            const errMsg = err.response?.data?.error || "Failed to add member";
            setError(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <Card className={styles.modalContent} title="Add Member">
                <button className={styles.closeBtn} onClick={onClose}>
                    <X size={20} />
                </button>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div className={styles.infoText}>
                        <small style={{ color: '#64748b', marginBottom: '0.5rem', display: 'block' }}>
                            Please enter the User ID of the member you want to add.
                        </small>
                    </div>
                    
                    <Input
                        label="User ID"
                        value={userId}
                        onChange={e => setUserId(e.target.value)}
                        placeholder="e.g. 550e8400-e29b-..."
                        required
                    />
                    
                    {error && <div className={styles.error} style={{color: 'red', fontSize: '0.9rem'}}>{error}</div>}

                    <Button type="submit" variant="travel" disabled={loading}>
                        {loading ? 'Adding...' : 'Add Member'}
                    </Button>
                </form>
            </Card>
        </div>
    );
};

export default AddMemberModal;
