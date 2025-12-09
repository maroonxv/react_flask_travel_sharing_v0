import { Link } from 'react-router-dom';
import { Calendar, Users, DollarSign } from 'lucide-react';
import Card from './Card';
import styles from './TripCard.module.css';

const TripCard = ({ trip }) => {
    return (
        <Card className={styles.card}>
            <div className={styles.imageContainer}>
                {/* Default image if none provided */}
                <div className={styles.imagePlaceholder}>
                    {trip.name?.charAt(0).toUpperCase()}
                </div>
            </div>

            <div className={styles.content}>
                <div className={styles.header}>
                    <h3 className={styles.title}>{trip.name}</h3>
                    <span className={`${styles.status} ${styles[trip.status?.toLowerCase()]}`}>
                        {trip.status}
                    </span>
                </div>

                <p className={styles.description}>{trip.description || '暂无描述。'}</p>

                <div className={styles.meta}>
                    <div className={styles.metaItem}>
                        <Calendar size={16} />
                        <span>{new Date(trip.start_date).toLocaleDateString()}</span>
                    </div>
                    <div className={styles.metaItem}>
                        <Users size={16} />
                        <span>{trip.member_count || 1} 成员</span>
                    </div>
                    <div className={styles.metaItem}>
                        <DollarSign size={16} />
                        <span>￥{trip.budget_amount || 0}</span>
                    </div>
                </div>

                <Link to={`/travel/trips/${trip.id}`} className={styles.linkOverlay} />
            </div>
        </Card>
    );
};

export default TripCard;
