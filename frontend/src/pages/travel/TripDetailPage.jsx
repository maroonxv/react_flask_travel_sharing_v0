import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTrip } from '../../api/travel';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import AddActivityModal from './AddActivityModal';
import AddMemberModal from './AddMemberModal';
import { Calendar, Users, DollarSign, MapPin, Clock, ArrowRight, ArrowLeft, Plus } from 'lucide-react';
import styles from './TripDetail.module.css';

const TripDetailPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [trip, setTrip] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeDayIdx, setActiveDayIdx] = useState(0);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showMemberModal, setShowMemberModal] = useState(false);

    useEffect(() => {
        fetchTrip();
    }, [id]);

    const fetchTrip = async () => {
        try {
            const data = await getTrip(id);
            setTrip(data);
        } catch (error) {
            console.error("Failed to load trip", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className={styles.loading}>加载旅行详情...</div>;
    if (!trip) return <div className={styles.container}>未找到旅行</div>;

    const days = trip.days || [];
    const currentDay = days[activeDayIdx];

    // Helper to format currency
    const fmtMoney = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

    return (
        <div className={styles.container}>
            <button style={{ marginBottom: '1rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem' }} onClick={() => navigate(-1)}>
                <ArrowLeft size={16} /> 返回
            </button>

            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <div>
                        <h1 className={styles.title}>{trip.name}</h1>
                        <div className={styles.dates}>
                            <Calendar size={18} />
                            <span>{new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>

                <div className={styles.metaRow}>
                    <div className={styles.metaBlock}>
                        <h3>预算</h3>
                        <p>{fmtMoney(trip.budget_amount)}</p>
                    </div>
                    <div className={styles.metaBlock}>
                        <h3>成员</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Users size={20} />
                            <span>{trip.member_count}</span>
                            <button 
                                onClick={() => setShowMemberModal(true)}
                                className={styles.iconBtn}
                                style={{ marginLeft: '0.5rem', cursor: 'pointer', background: 'none', border: 'none', color: '#3b82f6' }}
                                title="添加成员"
                            >
                                <Plus size={18} />
                            </button>
                        </div>
                    </div>
                    <div className={styles.metaBlock}>
                        <h3>状态</h3>
                        <p style={{ textTransform: 'capitalize' }}>{trip.status}</p>
                    </div>
                </div>
            </div>

            {/* Day Tabs */}
            <div className={styles.tabs}>
                {days.map((day, idx) => (
                    <button
                        key={idx}
                        className={`${styles.tab} ${activeDayIdx === idx ? styles.activeTab : ''}`}
                        onClick={() => setActiveDayIdx(idx)}
                    >
                        第 {idx + 1} 天
                    </button>
                ))}
            </div>

            {/* Timeline View */}
            <div className={styles.timeline}>
                {currentDay && (
                    <>
                        {/* Activities */}
                        {currentDay.activities && currentDay.activities.length > 0 ? (
                            currentDay.activities.map((activity, idx) => (
                                <div key={`act-${idx}`}>
                                    {/* Activity Item */}
                                    <div className={styles.timelineItem}>
                                        <div className={styles.timelineParams}>
                                            <span className={styles.time}>{activity.start_time?.slice(0, 5)}</span>
                                        </div>
                                        <div className={styles.dot} />
                                        <div className={styles.activityCard}>
                                            <h4 className={styles.activityName}>{activity.name}</h4>
                                            <div className={styles.location}>
                                                <MapPin size={14} />
                                                {activity.location_name}
                                            </div>
                                            <div className={styles.cost}>
                                                {fmtMoney(activity.cost)}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Transit between this and next? Check transits array properly based on backend return */}
                                    {/* For now, assuming transits array corresponds to gaps between activities or simply listing them */}
                                    {/* Let's try to find a transit that starts after this activity */}
                                </div>
                            ))
                        ) : (
                            <p style={{ color: '#94a3b8', fontStyle: 'italic', marginLeft: '1rem' }}>这一天还没有安排活动。</p>
                        )}

                        {/* Transits typically between activities, but here just rendering separate if simple mapping fails */}
                        {/* Displaying Transits at the bottom of the day if logic is complex */}
                        {currentDay.transits && currentDay.transits.length > 0 && (
                            <div style={{ marginTop: '2rem', paddingLeft: '1rem' }}>
                                <h3>交通</h3>
                                {currentDay.transits.map((transit, tIdx) => (
                                    <div key={`transit-${tIdx}`} className={styles.transitContainer}>
                                        <ArrowRight size={16} />
                                        <span>{transit.mode} ({transit.duration} mins)</span>
                                        <span>{transit.distance} km</span>
                                    </div>
                                ))}
                            </div>
                        )}

                    </>
                )}

                {/* Add Activity Button */}
                <div className={styles.addBtnContainer}>
                    <Button variant="travel" onClick={() => setShowAddModal(true)}>
                        + 添加活动
                    </Button>
                </div>
            </div>

            {showAddModal && (
                <AddActivityModal
                    tripId={id}
                    dayIndex={activeDayIdx} // Assuming backend uses 0-based index
                    onClose={() => setShowAddModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

            {showMemberModal && (
                <AddMemberModal
                    tripId={id}
                    onClose={() => setShowMemberModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

        </div>
    );
};

export default TripDetailPage;
