import { useState } from 'react';
import { addActivity } from '../../api/travel';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import { X } from 'lucide-react';
import styles from './TripDetail.module.css'; // Share styles

const AddActivityModal = ({ tripId, dayIndex, onClose, onSuccess }) => {
    const [formData, setFormData] = useState({
        name: '',
        activity_type: 'sightseeing', // Default
        location_name: '',
        start_time: '',
        end_time: '',
        cost: 0,
        currency: 'USD'
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await addActivity(tripId, dayIndex, formData);
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Failed to add activity", error);
            alert("添加活动失败");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <Card className={styles.modalContent} title="添加活动">
                <button className={styles.closeBtn} onClick={onClose}>
                    <X size={20} />
                </button>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <Input
                        label="活动名称"
                        value={formData.name}
                        onChange={e => setFormData({ ...formData, name: e.target.value })}
                        required
                    />
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <Input
                            label="类型"
                            value={formData.activity_type}
                            onChange={e => setFormData({ ...formData, activity_type: e.target.value })}
                            required
                        />
                        <Input
                            label="地点"
                            value={formData.location_name}
                            onChange={e => setFormData({ ...formData, location_name: e.target.value })}
                            required
                        />
                    </div>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <Input
                            label="开始时间"
                            type="time"
                            value={formData.start_time}
                            onChange={e => setFormData({ ...formData, start_time: e.target.value })}
                            required
                        />
                        <Input
                            label="结束时间"
                            type="time"
                            value={formData.end_time}
                            onChange={e => setFormData({ ...formData, end_time: e.target.value })}
                            required
                        />
                    </div>
                    <Input
                        label="花费"
                        type="number"
                        value={formData.cost}
                        onChange={e => setFormData({ ...formData, cost: e.target.value })}
                    />

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                        <Button type="button" variant="secondary" onClick={onClose}>
                            取消
                        </Button>
                        <Button type="submit" variant="travel" disabled={loading}>
                            {loading ? '添加中...' : '添加活动'}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default AddActivityModal;
