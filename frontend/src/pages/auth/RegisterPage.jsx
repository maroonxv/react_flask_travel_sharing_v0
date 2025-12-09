import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';
import styles from './Auth.module.css';

const RegisterPage = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        role: 'user' // default role
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            return setError("Passwords do not match");
        }

        setError('');
        setLoading(true);

        try {
            // API expects: username, email, password, role
            await register({
                username: formData.username,
                email: formData.email,
                password: formData.password,
                role: formData.role
            });
            navigate('/social');
        } catch (err) {
            console.error('Registration failed', err);
            const errMsg = err.response?.data?.error || err.message || 'Registration failed. Please try again.';
            setError(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.authCard} title="Create Account">
                <form onSubmit={handleSubmit} className={styles.form}>
                    <Input
                        label="Username"
                        name="username"
                        type="text"
                        placeholder="Choose a username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="Email"
                        name="email"
                        type="email"
                        placeholder="Enter your email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="Password"
                        name="password"
                        type="password"
                        placeholder="Create a password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="Confirm Password"
                        name="confirmPassword"
                        type="password"
                        placeholder="Confirm your password"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        required
                    />

                    {error && <div className={styles.error}>{error}</div>}

                    <Button type="submit" variant="primary" className={styles.submitBtn} disabled={loading}>
                        {loading ? 'Creating Account...' : 'Register'}
                    </Button>

                    <div className={styles.footer}>
                        Already have an account? <Link to="/auth/login" className={styles.link}>Login here</Link>
                    </div>
                </form>
            </Card>
        </div>
    );
};

export default RegisterPage;
