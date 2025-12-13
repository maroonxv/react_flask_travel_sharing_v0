import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Home, Globe, Map, User, LogOut, MessageSquare, ChevronLeft, ChevronRight, Bot } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import styles from './Layout.module.css';

const Layout = () => {
    const { user, logout } = useAuth();
    const location = useLocation();
    const [isCollapsed, setIsCollapsed] = useState(false);

    const isActive = (path) => location.pathname.startsWith(path);

    return (
        <div className={styles.container}>
            <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
                <div className={styles.header}>
                    <div className={styles.logo}>
                        {isCollapsed ? 'TS' : 'TravelShare'}
                    </div>
                    <button 
                        className={styles.collapseBtn}
                        onClick={() => setIsCollapsed(!isCollapsed)}
                    >
                        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </button>
                </div>
                
                <nav className={styles.nav}>
                    <Link to="/social" className={`${styles.link} ${isActive('/social') ? styles.activeSocial : ''}`} title="社区">
                        <Globe size={20} />
                        <span className={styles.linkText}>社区</span>
                    </Link>
                    <Link to="/travel" className={`${styles.link} ${isActive('/travel') ? styles.activeTravel : ''}`} title="旅行">
                        <Map size={20} />
                        <span className={styles.linkText}>旅行</span>
                    </Link>
                    <Link to="/chat" className={`${styles.link} ${isActive('/chat') ? styles.activeChat : ''}`} title="消息">
                        <MessageSquare size={20} />
                        <span className={styles.linkText}>消息</span>
                    </Link>
                    <Link to="/ai-assistant" className={`${styles.link} ${isActive('/ai-assistant') ? styles.activeAi : ''}`} title="AI助手">
                        <Bot size={20} />
                        <span className={styles.linkText}>AI助手</span>
                    </Link>
                    <Link to={`/profile/${user?.id}`} className={`${styles.link} ${isActive('/profile') ? styles.activeProfile : ''}`} title="我的">
                        <User size={20} />
                        <span className={styles.linkText}>我的</span>
                    </Link>
                </nav>
                <div className={styles.footer}>
                    <button onClick={logout} className={styles.logoutBtn} title="退出登录">
                        <LogOut size={20} />
                        <span className={styles.linkText}>退出登录</span>
                    </button>
                </div>
            </aside>
            <main className={styles.main}>
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
