import { Link, useLocation, Outlet } from 'react-router-dom';
import { Home, Globe, Map, User, LogOut, MessageSquare } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import styles from './Layout.module.css';

const Layout = () => {
    const { user, logout } = useAuth();
    const location = useLocation();

    const isActive = (path) => location.pathname.startsWith(path);

    return (
        <div className={styles.container}>
            <aside className={styles.sidebar}>
                <div className={styles.logo}>TravelShare</div>
                <nav className={styles.nav}>
                    <Link to="/social" className={`${styles.link} ${isActive('/social') ? styles.activeSocial : ''}`}>
                        <Globe size={20} />
                        <span>社区</span>
                    </Link>
                    <Link to="/travel" className={`${styles.link} ${isActive('/travel') ? styles.activeTravel : ''}`}>
                        <Map size={20} />
                        <span>旅行</span>
                    </Link>
                    <Link to="/chat" className={`${styles.link} ${isActive('/chat') ? styles.activeChat : ''}`}>
                        <MessageSquare size={20} />
                        <span>消息</span>
                    </Link>
                    <Link to="/profile" className={`${styles.link} ${isActive('/profile') ? styles.activeProfile : ''}`}>
                        <User size={20} />
                        <span>我的</span>
                    </Link>
                </nav>
                <div className={styles.footer}>
                    <button onClick={logout} className={styles.logoutBtn}>
                        <LogOut size={20} />
                        <span>退出登录</span>
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
