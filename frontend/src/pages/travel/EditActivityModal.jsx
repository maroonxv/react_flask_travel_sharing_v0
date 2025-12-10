import { useState, useEffect } from 'react';
import { updateActivity } from '../../api/travel';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import { X } from 'lucide-react';
import styles from './TripDetail.module.css'; // Share styles

const EditActivityModal = ({ tripId, dayIndex, activity, onClose, onSuccess }) => {
    const [formData, setFormData] = useState({
        name: '',
        activity_type: 'sightseeing',
        location_name: '',
        start_time: '',
        end_time: '',
        cost: 0,
        currency: 'USD'
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (activity) {
            setFormData({
                name: activity.name,
                activity_type: activity.type || 'sightseeing',
                location_name: activity.location?.name || '',
                start_time: activity.start_time || '',
                end_time: activity.end_time || '',
                cost: activity.cost?.amount || 0,
                currency: activity.cost?.currency || 'USD'
            });
        }
    }, [activity]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...formData,
                cost_amount: formData.cost,
                cost: undefined
            };
            await updateActivity(tripId, dayIndex, activity.id, payload);
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Failed to update activity", error);
            alert("修改活动失败");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <Card className={styles.modalContent} title="修改活动">
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
                            {loading ? '保存中...' : '保存修改'}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default EditActivityModal;
