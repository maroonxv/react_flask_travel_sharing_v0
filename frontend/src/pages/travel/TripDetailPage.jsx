import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTrip, updateTrip } from '../../api/travel';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/Button';
import LoadingSpinner from '../../components/LoadingSpinner';
import AddActivityModal from './AddActivityModal';
import EditActivityModal from './EditActivityModal';
import AddMemberModal from './AddMemberModal';
import TripMembersModal from './TripMembersModal';
import EditTripModal from './EditTripModal';
import { Calendar, Users, DollarSign, MapPin, Clock, ArrowRight, ArrowLeft, Plus, Edit2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import styles from './TripDetail.module.css';

const TripDetailPage = () => {
    const { tripId: id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [trip, setTrip] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeDayIdx, setActiveDayIdx] = useState(0);
    const [showAddModal, setShowAddModal] = useState(false);
    const [showAddMemberModal, setShowAddMemberModal] = useState(false);
    const [showMembersListModal, setShowMembersListModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [isEditingStatus, setIsEditingStatus] = useState(false);
    const [editingActivity, setEditingActivity] = useState(null);

    useEffect(() => {
        fetchTrip();
    }, [id]);

    const fetchTrip = async () => {
        try {
            const data = await getTrip(id);
            setTrip(data);
        } catch (error) {
            console.error("Failed to load trip", error);
            toast.error("加载旅行详情失败");
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = async (newStatus) => {
        try {
            const updatedTrip = await updateTrip(trip.id, { status: newStatus });
            setTrip(updatedTrip);
            setIsEditingStatus(false);
            toast.success("状态已更新");
        } catch (error) {
            console.error("Failed to update status", error);
            toast.error("更新状态失败");
        }
    };

    if (loading) return <div className={styles.loading}><LoadingSpinner size="large" /></div>;
    if (!trip) return <div className={styles.container}>未找到旅行</div>;

    const days = trip.days || [];
    const currentDay = days[activeDayIdx];

    // Helper to format currency
    const fmtMoney = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

    const currentUserMember = trip.members?.find(m => m.user_id === user?.id);
    const isCurrentUserAdmin = user?.id === trip.creator_id || currentUserMember?.role === 'admin' || currentUserMember?.role === 'owner';

    const STATUS_OPTIONS = [
        { value: 'planning', label: '计划中' },
        { value: 'in_progress', label: '进行中' },
        { value: 'completed', label: '已完成' },
        { value: 'cancelled', label: '已取消' }
    ];

    const TRANSIT_MODE_MAP = {
        'walking': '步行',
        'driving': '驾车',
        'transit': '公共交通',
        'cycling': '骑行',
        'WALKING': '步行',
        'DRIVING': '驾车',
        'TRANSIT': '公共交通',
        'CYCLING': '骑行'
    };

    const getTransitFrom = (activityId) => {
        return currentDay.transits?.find(t => t.from_activity_id === activityId);
    };

    // Calculate total cost
    const totalCost = trip.days?.reduce((acc, day) => {
        const activityCost = day.activities?.reduce((sum, act) => sum + (act.cost?.amount || 0), 0) || 0;
        const transitCost = day.transits?.reduce((sum, trans) => sum + (trans.cost?.amount || 0), 0) || 0;
        return acc + activityCost + transitCost;
    }, 0) || 0;

    const isOverBudget = totalCost > (trip.budget_amount || 0);

    return (
        <div className={styles.container}>
            {/* Hero Cover Image */}
            {trip.cover_image_url && (
                <div 
                    style={{
                        width: '100%',
                        height: '300px',
                        marginBottom: '2rem',
                        borderRadius: '0.5rem',
                        overflow: 'hidden',
                        position: 'relative',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                    }}
                >
                    <img 
                        src={trip.cover_image_url} 
                        alt={trip.name} 
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                        }}
                    />
                    <div 
                        style={{
                            position: 'absolute',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            padding: '2rem',
                            background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
                            color: 'white'
                        }}
                    >
                        <h1 style={{ margin: 0, fontSize: '2.5rem', fontWeight: 'bold' }}>{trip.name}</h1>
                        <p style={{ margin: '0.5rem 0 0 0', opacity: 0.9 }}>{trip.description}</p>
                    </div>
                </div>
            )}

            <button style={{ marginBottom: '1rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => navigate(-1)}>
                <ArrowLeft size={16} /> 返回
            </button>

            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <h1 className={styles.title}>{trip.name}</h1>
                            {isCurrentUserAdmin && (
                                <button 
                                    onClick={() => setShowEditModal(true)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                                    title="编辑旅行信息"
                                >
                                    <Edit2 size={20} />
                                </button>
                            )}
                        </div>
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
                        <h3>实际花费</h3>
                        <p style={{ color: isOverBudget ? '#ef4444' : '#22c55e', fontWeight: 'bold' }}>
                            {fmtMoney(totalCost)}
                        </p>
                    </div>
                    <div className={styles.metaBlock}>
                        <h3>成员</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div 
                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
                                onClick={() => setShowMembersListModal(true)}
                                title="查看成员列表"
                            >
                                <Users size={20} />
                                <span>{trip.member_count}</span>
                            </div>
                            {isCurrentUserAdmin && (
                                <button 
                                    onClick={() => setShowAddMemberModal(true)}
                                    className={styles.iconBtn}
                                    style={{ marginLeft: '0.5rem', cursor: 'pointer', background: 'none', border: 'none', color: '#3b82f6' }}
                                    title="添加成员"
                                >
                                    <Plus size={18} />
                                </button>
                            )}
                        </div>
                    </div>
                    <div className={styles.metaBlock}>
                        <h3>状态</h3>
                        {isEditingStatus ? (
                            <select 
                                value={trip.status} 
                                onChange={(e) => handleStatusChange(e.target.value)}
                                onBlur={() => setIsEditingStatus(false)}
                                autoFocus
                                style={{ padding: '0.25rem', borderRadius: '4px', border: '1px solid #ccc' }}
                            >
                                {STATUS_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <p style={{ textTransform: 'capitalize' }}>{trip.status}</p>
                                {isCurrentUserAdmin && (
                                    <button 
                                        onClick={() => setIsEditingStatus(true)}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
                                        title="修改状态"
                                    >
                                        <Edit2 size={14} />
                                    </button>
                                )}
                            </div>
                        )}
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
                            currentDay.activities.map((activity, idx) => {
                                const transit = getTransitFrom(activity.id);
                                const prevActivity = idx > 0 ? currentDay.activities[idx - 1] : null;
                                const isTimeConflict = prevActivity && activity.start_time < prevActivity.end_time;

                                return (
                                    <div key={`act-${idx}`}>
                                        {/* Activity Item */}
                                        <div className={styles.timelineItem}>
                                            <div className={styles.timelineParams}>
                                                <span className={styles.time} style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                                                    {activity.start_time?.slice(0, 5)}
                                                </span>
                                                <span className={styles.time} style={{ fontSize: '0.9rem', color: '#64748b' }}>
                                                    - {activity.end_time?.slice(0, 5)}
                                                </span>
                                                {isTimeConflict && (
                                                    <div style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                                                        时间冲突
                                                    </div>
                                                )}
                                            </div>
                                            <div className={styles.dot} />
                                            <div 
                                                className={styles.activityCard}
                                                onClick={() => isCurrentUserAdmin && setEditingActivity(activity)}
                                                style={{ cursor: isCurrentUserAdmin ? 'pointer' : 'default', border: isTimeConflict ? '1px solid #ef4444' : undefined }}
                                                title={isCurrentUserAdmin ? "点击修改活动" : "仅管理员可修改"}
                                            >
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

                                        {/* Transit between this and next */}
                                        {transit && (
                                            <div className={styles.timelineItem} style={{ minHeight: 'auto', margin: '0.5rem 0' }}>
                                                 <div className={styles.timelineParams}></div>
                                                 <div className={styles.dot} style={{ background: 'transparent', border: 'none', display: 'flex', justifyContent: 'center' }}>
                                                    <div style={{ width: '2px', height: '100%', background: '#e2e8f0' }}></div>
                                                 </div>
                                                 <div style={{ paddingLeft: '1rem', color: '#fff', fontSize: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500 }}>
                                                        <ArrowRight size={16} />
                                                        <span>{TRANSIT_MODE_MAP[transit.mode] || transit.mode}</span>
                                                        <span>({Math.round(transit.duration_seconds / 60)} 分钟)</span>
                                                        <span>{(transit.distance_meters / 1000).toFixed(1)} km</span>
                                                    </div>
                                                    {(transit.mode === 'driving' || transit.mode === 'DRIVING') && transit.cost && (
                                                        <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginLeft: '1.5rem' }}>
                                                            交通费: 5元, 油费: {transit.cost.fuel_cost || 0}元
                                                        </div>
                                                    )}
                                                 </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                        ) : (
                            <p style={{ color: '#94a3b8', fontStyle: 'italic', marginLeft: '1rem' }}>这一天还没有安排活动。</p>
                        )}
                    </>
                )}

                {/* Add Activity Button */}
                {isCurrentUserAdmin && (
                    <div className={styles.addBtnContainer}>
                        <Button variant="travel" onClick={() => setShowAddModal(true)}>
                            + 添加活动
                        </Button>
                    </div>
                )}
            </div>

            {showAddModal && (
                <AddActivityModal
                    tripId={id}
                    dayIndex={activeDayIdx} // Assuming backend uses 0-based index
                    onClose={() => setShowAddModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

            {editingActivity && (
                <EditActivityModal
                    tripId={id}
                    dayIndex={activeDayIdx}
                    activity={editingActivity}
                    onClose={() => setEditingActivity(null)}
                    onSuccess={fetchTrip}
                />
            )}

            {showAddMemberModal && (
                <AddMemberModal
                    tripId={id}
                    onClose={() => setShowAddMemberModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

            {showMembersListModal && (
                <TripMembersModal
                    trip={trip}
                    onClose={() => setShowMembersListModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

            {showEditModal && (
                <EditTripModal
                    trip={trip}
                    onClose={() => setShowEditModal(false)}
                    onSuccess={fetchTrip}
                />
            )}

        </div>
    );
};

export default TripDetailPage;
