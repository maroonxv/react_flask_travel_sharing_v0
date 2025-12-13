import { Link } from 'react-router-dom';
import { Calendar, Users, DollarSign } from 'lucide-react';
import Card from './Card';
import styles from './TripCard.module.css';

const TripCard = ({ trip }) => {
    const STATUS_MAP = {
        'planning': '计划中',
        'in_progress': '进行中',
        'completed': '已完成',
        'cancelled': '已取消',
        'PLANNING': '计划中',
        'IN_PROGRESS': '进行中',
        'COMPLETED': '已完成',
        'CANCELLED': '已取消'
    };

    return (
        <Link to={`/travel/${trip.id}`} style={{ textDecoration: 'none', display: 'block' }}>
            <Card className={styles.card}>
                <div className={styles.imageContainer}>
                    {trip.cover_image_url ? (
                        <img src={trip.cover_image_url} alt={trip.name} className={styles.coverImage} />
                    ) : (
                        /* Default image if none provided */
                        <div className={styles.imagePlaceholder}>
                            {trip.name?.charAt(0).toUpperCase()}
                        </div>
                    )}
                </div>

                <div className={styles.content}>
                    <div className={styles.header}>
                        <h3 className={styles.title}>{trip.name}</h3>
                        <span className={`${styles.status} ${styles[trip.status?.toLowerCase()]}`}>
                            {STATUS_MAP[trip.status] || trip.status}
                        </span>
                    </div>

                    <p className={styles.description}>{trip.description || '暂无描述。'}</p>

                    <div className={styles.meta}>
                        <div className={styles.metaItem}>
                            <Users size={14} />
                            <span>{trip.member_count || 1}人</span>
                        </div>
                        <div className={styles.metaItem}>
                            <DollarSign size={14} />
                            <span>{trip.budget_amount || 0}</span>
                        </div>
                        <div className={styles.dates}>
                            {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
                        </div>
                    </div>
                </div>
            </Card>
        </Link>
    );
};

export default TripCard;
