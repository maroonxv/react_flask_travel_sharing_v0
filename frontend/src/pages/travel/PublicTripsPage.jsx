import { useState, useEffect } from 'react';
import { getPublicTrips } from '../../api/travel';
import TripCard from '../../components/TripCard';
import styles from './TravelList.module.css';

const PublicTripsPage = ({ searchQuery }) => {
    const [trips, setTrips] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTrips = async () => {
            setLoading(true);
            try {
                const data = await getPublicTrips(searchQuery);
                setTrips(Array.isArray(data) ? data : (data.trips || []));
            } catch (error) {
                console.error("Failed to fetch public trips", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTrips();
    }, [searchQuery]);

    return (
        <div>
            {loading ? (
                <div className={styles.loading}>加载旅行中...</div>
            ) : (
                <div className={styles.grid}>
                    {trips.length > 0 ? (
                        trips.map(trip => <TripCard key={trip.id} trip={trip} />)
                    ) : (
                        <div className={styles.empty}>
                            {searchQuery ? '没有找到匹配的旅行。' : '暂无公开旅行。'}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default PublicTripsPage;
