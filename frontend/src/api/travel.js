import client from './client';

export const getUserTrips = async (userId) => {
    // If userId not provided, maybe use 'me'? Endpoint: /travel/users/:my_id/trips
    // We can get current user ID from context, but for now let's assume the component passes it.
    const response = await client.get(`/travel/users/${userId}/trips`);
    return response.data;
};

export const getPublicTrips = async () => {
    const response = await client.get('/travel/trips/public');
    return response.data;
};

export const getTrip = async (id) => {
    const response = await client.get(`/travel/trips/${id}`);
    return response.data;
};

export const createTrip = async (tripData) => {
    const response = await client.post('/travel/trips', tripData);
    return response.data;
};

export const addActivity = async (tripId, dayIndex, activityData) => {
    const response = await client.post(`/travel/trips/${tripId}/days/${dayIndex}/activities`, activityData);
    return response.data;
};

export const addMember = async (tripId, userId, role = 'member') => {
    const response = await client.post(`/travel/trips/${tripId}/members`, { user_id: userId, role });
    return response.data;
};

export const removeMember = async (tripId, userId) => {
    const response = await client.delete(`/travel/trips/${tripId}/members/${userId}`);
    return response.data;
};
