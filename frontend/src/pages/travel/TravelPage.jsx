import { useState } from 'react';
import MyTripsPage from './MyTripsPage';
import PublicTripsPage from './PublicTripsPage';
import styles from './TravelList.module.css';
import { Search } from 'lucide-react';

const TravelPage = () => {
    const [activeTab, setActiveTab] = useState('discover');
    const [searchQuery, setSearchQuery] = useState('');
    const [tempSearch, setTempSearch] = useState('');

    const handleSearch = (e) => {
        e.preventDefault();
        setSearchQuery(tempSearch);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header} style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '1rem' }}>
                <h1 className={styles.title}>旅行</h1>
                
                <div style={{ display: 'flex', gap: '1rem', width: '100%', borderBottom: '1px solid #e2e8f0' }}>
                    <button 
                        onClick={() => setActiveTab('discover')}
                        style={{
                            padding: '0.5rem 1rem',
                            borderBottom: activeTab === 'discover' ? '2px solid #3b82f6' : 'none',
                            color: activeTab === 'discover' ? '#3b82f6' : '#64748b',
                            fontWeight: activeTab === 'discover' ? '600' : '400',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '1.1rem'
                        }}
                    >
                        发现
                    </button>
                    <button 
                        onClick={() => setActiveTab('my_trips')}
                        style={{
                            padding: '0.5rem 1rem',
                            borderBottom: activeTab === 'my_trips' ? '2px solid #3b82f6' : 'none',
                            color: activeTab === 'my_trips' ? '#3b82f6' : '#64748b',
                            fontWeight: activeTab === 'my_trips' ? '600' : '400',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '1.1rem'
                        }}
                    >
                        我的旅行
                    </button>
                </div>
            </div>

            {activeTab === 'discover' && (
                <div style={{ marginBottom: '1.5rem' }}>
                    <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', maxWidth: '400px' }}>
                        <div style={{ position: 'relative', flex: 1 }}>
                            <Search size={18} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                            <input 
                                type="text"
                                value={tempSearch}
                                onChange={(e) => setTempSearch(e.target.value)}
                                placeholder="搜索公开旅行（名称或描述）..."
                                style={{
                                    width: '100%',
                                    padding: '0.5rem 0.5rem 0.5rem 2.25rem',
                                    borderRadius: '0.375rem',
                                    border: '1px solid #cbd5e1',
                                    outline: 'none',
                                    fontSize: '1rem'
                                }}
                            />
                        </div>
                        <button 
                            type="submit"
                            style={{
                                padding: '0.5rem 1rem',
                                backgroundColor: '#3b82f6',
                                color: 'white',
                                borderRadius: '0.375rem',
                                border: 'none',
                                cursor: 'pointer',
                                fontSize: '1rem'
                            }}
                        >
                            搜索
                        </button>
                    </form>
                </div>
            )}

            {activeTab === 'discover' ? (
                <div>
                    <PublicTripsPage searchQuery={searchQuery} />
                </div>
            ) : (
                <div>
                    <MyTripsPage />
                </div>
            )}
        </div>
    );
};

export default TravelPage;
