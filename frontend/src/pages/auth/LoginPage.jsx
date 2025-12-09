import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';
import styles from './Auth.module.css';

const LoginPage = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            navigate('/social');
        } catch (err) {
            console.error('Login failed', err);
            const errMsg = err.response?.data?.error || err.message || 'Login failed. Please check your credentials.';
            setError(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.authCard} title="Welcome Back">
                <form onSubmit={handleSubmit} className={styles.form}>
                    <Input
                        label="Email"
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <Input
                        label="Password"
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                    {error && <div className={styles.error}>{error}</div>}

                    <Button type="submit" variant="primary" className={styles.submitBtn} disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'}
                    </Button>

                    <div className={styles.footer}>
                        Don't have an account? <Link to="/auth/register" className={styles.link}>Register here</Link>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default LoginPage;
