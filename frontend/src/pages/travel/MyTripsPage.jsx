import { useState, useEffect } from 'react';
import { getUserTrips, createTrip, uploadTripCover } from '../../api/travel';
import { useAuth } from '../../context/AuthContext';
import TripCard from '../../components/TripCard';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import { Plus, X } from 'lucide-react';
import styles from './TravelList.module.css';

const MyTripsPage = () => {
    const { user } = useAuth();
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // New Trip Form State
    const [newTrip, setNewTrip] = useState({
        name: '',
        start_date: '',
        end_date: '',
        budget_amount: '',
        description: '',
        visibility: 'private'
    });
    const [coverFile, setCoverFile] = useState(null);

    useEffect(() => {
        if (user) loadTrips();
    }, [user]);

    const loadTrips = async () => {
        try {
            const data = await getUserTrips(user.id);
            setTrips(Array.isArray(data) ? data : (data.trips || []));
        } catch (error) {
            console.error("Failed to load trips", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            let coverUrl = null;
            if (coverFile) {
                const uploadRes = await uploadTripCover(coverFile);
                coverUrl = uploadRes.url;
            }

            const payload = { 
                ...newTrip, 
                creator_id: user.id,
                cover_image_url: coverUrl
            };
            if (!payload.budget_amount) {
                delete payload.budget_amount;
            }
            await createTrip(payload);
            setShowModal(false);
            setNewTrip({ name: '', start_date: '', end_date: '', budget_amount: '', description: '', visibility: 'private' });
            setCoverFile(null);
            loadTrips(); // Refresh
        } catch (error) {
            console.error("Failed to create trip", error);
            const errMsg = error.response?.data?.error || error.message || "Unknown error";
            alert(`创建旅行失败: ${errMsg}`);
        }
    };

    return (
        <div>
            <div className={styles.header} style={{ borderBottom: 'none', marginBottom: '1rem', paddingBottom: 0 }}>
                <div /> {/* Spacer or empty title */}
                <Button variant="travel" onClick={() => setShowModal(true)}>
                    <Plus size={20} style={{ marginRight: '0.5rem' }} />
                    新建旅行
                </Button>
            </div>

            {loading ? (
                <div className={styles.loading}>加载旅行列表...</div>
            ) : (
                <div className={styles.grid}>
                    {trips.length > 0 ? (
                        trips.map(trip => <TripCard key={trip.id} trip={trip} />)
                    ) : (
                        <div className={styles.empty}>你还没有创建任何旅行计划。</div>
                    )}
                </div>
            )}

            {/* Simple Modal overlay for creating trip */}
            {showModal && (
                <div className={styles.modalOverlay}>
                    <Card className={styles.modalContent} title="计划一次新旅行">
                        <button className={styles.closeBtn} onClick={() => setShowModal(false)}>
                            <X size={20} />
                        </button>
                        <form onSubmit={handleCreate} className={styles.form}>
                            <Input
                                label="旅行名称"
                                value={newTrip.name}
                                onChange={e => setNewTrip({ ...newTrip, name: e.target.value })}
                                required
                            />
                            <div className={styles.row}>
                                <Input
                                    label="开始日期"
                                    type="date"
                                    value={newTrip.start_date}
                                    onChange={e => setNewTrip({ ...newTrip, start_date: e.target.value })}
                                    required
                                />
                                <Input
                                    label="结束日期"
                                    type="date"
                                    value={newTrip.end_date}
                                    onChange={e => setNewTrip({ ...newTrip, end_date: e.target.value })}
                                    required
                                />
                            </div>
                            <Input
                                label="预算 (￥)"
                                type="number"
                                value={newTrip.budget_amount}
                                onChange={e => setNewTrip({ ...newTrip, budget_amount: e.target.value })}
                            />
                            <Input
                                label="描述"
                                value={newTrip.description}
                                onChange={e => setNewTrip({ ...newTrip, description: e.target.value })}
                            />
                            
                            <div style={{ marginBottom: '1rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>可见性</label>
                                <select
                                    value={newTrip.visibility}
                                    onChange={e => setNewTrip({ ...newTrip, visibility: e.target.value })}
                                    style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                                >
                                    <option value="private">私有 (Private)</option>
                                    <option value="public">公开 (Public)</option>
                                    <option value="shared">共享 (Shared)</option>
                                </select>
                            </div>

                            <div style={{ marginBottom: '1rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>封面图片</label>
                                <input
                                    type="file"
                                    accept="image/*"
                                    onChange={e => setCoverFile(e.target.files[0])}
                                    style={{ width: '100%' }}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                                <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
                                    取消
                                </Button>
                                <Button type="submit" variant="travel">
                                    创建旅行
                                </Button>
                            </div>
                        </form>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default MyTripsPage;
