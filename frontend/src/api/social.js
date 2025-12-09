import client from './client';

export const getFeed = async (limit = 20, offset = 0) => {
    const response = await client.get(`/social/feed?limit=${limit}&offset=${offset}`);
    return response.data;
};

export const getUserPosts = async (userId, limit = 20, offset = 0) => {
    const response = await client.get(`/social/users/${userId}/posts?limit=${limit}&offset=${offset}`);
    return response.data;
};

export const createPost = async (formData) => {
    // formData handles multipart/form-data for images
    const response = await client.post('/social/posts', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const getPost = async (id) => {
    const response = await client.get(`/social/posts/${id}`);
    return response.data;
};

export const likePost = async (id) => {
    const response = await client.post(`/social/posts/${id}/like`);
    return response.data;
};

export const getComments = async (postId) => {
    // Assuming comments are part of post detail or fetched separately? 
    // The prompt says "GET /posts/:id" returns post details.
    // And "POST /posts/:id/comments" to add.
    // If comments are separate, we might need a separate endpoint, but usually included in details.
    // Let's assume we can also fetch them via a sub-resource if needed, but for now relies on details.
    // However, for interactions we need endpoints.
};

export const addComment = async (postId, content) => {
    const response = await client.post(`/social/posts/${postId}/comments`, { content });
    return response.data;
};

export const getConversations = async () => {
    const response = await client.get('/social/conversations');
    return response.data;
};

export const getMessages = async (conversationId) => {
    const response = await client.get(`/social/conversations/${conversationId}/messages`);
    return response.data;
};

export const sendMessage = async (conversationId, content) => {
    const response = await client.post(`/social/conversations/${conversationId}/messages`, { content });
    return response.data;
};
