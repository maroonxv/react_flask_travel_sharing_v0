import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { createPost } from '../../api/social';
import { getUserTrips } from '../../api/travel';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import { Image as ImageIcon, MapPin, X } from 'lucide-react';
import styles from './CreatePostPage.module.css';

const CreatePostPage = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [tags, setTags] = useState('');
    const [selectedTrip, setSelectedTrip] = useState('');
    const [visibility, setVisibility] = useState('public');
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [myTrips, setMyTrips] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (user) {
            fetchTrips();
        }
    }, [user]);

    const fetchTrips = async () => {
        try {
            const trips = await getUserTrips(user.id);
            setMyTrips(Array.isArray(trips) ? trips : (trips.trips || []));
        } catch (error) {
            console.error("Failed to load trips", error);
        }
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImage(file);
            setPreview(URL.createObjectURL(file));
        }
    };

    const removeImage = () => {
        setImage(null);
        setPreview(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        formData.append('title', title);
        formData.append('content', content);
        formData.append('tags', tags); // Backend should handle comma separated or JSON
        formData.append('visibility', visibility); // public, private, friends
        if (selectedTrip) formData.append('trip_id', selectedTrip);
        if (image) formData.append('media_files', image); // "media_files" as per spec

        try {
            await createPost(formData);
            navigate('/social');
        } catch (error) {
            console.error("Failed to create post", error);
            alert("发布帖子失败");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.formCard} title="发布新帖子">
                <form onSubmit={handleSubmit} className={styles.form}>
                    <Input
                        label="标题"
                        placeholder="给你的帖子起个标题吧"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                    />

                    <div className={styles.textareaWrapper}>
                        <label className={styles.label}>内容</label>
                        <textarea
                            className={styles.textarea}
                            placeholder="分享你的旅行经历..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            required
                        />
                    </div>

                    {preview ? (
                        <div className={styles.imagePreview}>
                            <img src={preview} alt="Preview" />
                            <button type="button" className={styles.removeBtn} onClick={removeImage}>
                                <X size={16} />
                            </button>
                        </div>
                    ) : (
                        <div className={styles.uploadArea}>
                            <label htmlFor="image-upload" className={styles.uploadLabel}>
                                <ImageIcon size={24} />
                                <span>添加照片</span>
                            </label>
                            <input
                                id="image-upload"
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                style={{ display: 'none' }}
                            />
                        </div>
                    )}

                    <div className={styles.row}>
                        <div className={styles.selectWrapper}>
                            <label className={styles.label}>关联旅行 (可选)</label>
                            <div className={styles.selectContainer}>
                                <MapPin size={16} className={styles.selectIcon} />
                                <select
                                    className={styles.select}
                                    value={selectedTrip}
                                    onChange={(e) => setSelectedTrip(e.target.value)}
                                >
                                    <option value="">选择一个旅行...</option>
                                    {myTrips.map(trip => (
                                        <option key={trip.id} value={trip.id}>{trip.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <Input
                            label="标签 (逗号分隔)"
                            placeholder="travel, fun, japan"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            className={styles.tagsInput}
                        />
                    </div>

                    <div className={styles.actions}>
                        <Button type="button" variant="secondary" onClick={() => navigate('/social')}>
                            取消
                        </Button>
                        <Button type="submit" variant="social" disabled={loading}>
                            {loading ? '发布中...' : '发布'}
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default CreatePostPage;
