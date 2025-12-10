import { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkUser();
    }, []);

    const checkUser = async () => {
        try {
            const { data } = await client.get('/auth/me');
            setUser(data);
        } catch (error) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        await client.post('/auth/login', { email, password });
        await checkUser();
    };

    const register = async (userData) => {
        await client.post('/auth/register', userData);
        await checkUser(); // Or automatic login
    };

    const logout = async () => {
        await client.post('/auth/logout');
        setUser(null);
    };

    const updatePassword = async (oldPassword, newPassword) => {
        await client.post('/auth/change-password', {
            old_password: oldPassword,
            new_password: newPassword
        });
    };

    const updateProfile = async (profileData) => {
        const config = {};
        if (profileData instanceof FormData) {
            // When sending FormData, let the browser set the Content-Type with boundary
            // We explicitly set it to multipart/form-data to override the default application/json
            config.headers = { 'Content-Type': 'multipart/form-data' };
        }
        const { data } = await client.put('/auth/me/profile', profileData, config);
        setUser(data);
        return data;
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, register, logout, updatePassword, updateProfile, checkUser }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
