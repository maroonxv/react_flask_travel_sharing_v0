import { useState, useEffect } from 'react';
import { getUserTrips, createTrip } from '../../api/travel';
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
        description: ''
    });

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
            const payload = { ...newTrip, creator_id: user.id };
            if (!payload.budget_amount) {
                delete payload.budget_amount;
            }
            await createTrip(payload);
            setShowModal(false);
            setNewTrip({ name: '', start_date: '', end_date: '', budget_amount: '', description: '' });
            loadTrips(); // Refresh
        } catch (error) {
            console.error("Failed to create trip", error);
            const errMsg = error.response?.data?.error || error.message || "Unknown error";
            alert(`创建旅行失败: ${errMsg}`);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>我的旅行</h1>
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
                            <Button type="submit" variant="travel" style={{ marginTop: '1rem' }}>
                                创建旅行
                            </Button>
                        </form>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default MyTripsPage;
