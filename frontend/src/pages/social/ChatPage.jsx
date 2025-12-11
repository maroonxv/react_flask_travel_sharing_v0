import { useState, useEffect, useRef } from 'react';
import { 
    getConversations, 
    getMessages, 
    sendMessage, 
    getFriendRequests, 
    acceptFriendRequest, 
    rejectFriendRequest,
    getFriends,
    createConversation
} from '../../api/social';
import { useAuth } from '../../context/AuthContext';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';
import { Send, User, Check, X, MessageSquare } from 'lucide-react';
import styles from './ChatPage.module.css';

const ChatPage = () => {
    const { user } = useAuth();
    const [conversations, setConversations] = useState([]);
    const [requests, setRequests] = useState([]);
    const [friends, setFriends] = useState([]);
    const [activeConvId, setActiveConvId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadAllData();
    }, []);

    useEffect(() => {
        if (activeConvId) {
            loadMessages(activeConvId);
            // In a real app, join socket room here
        }
    }, [activeConvId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const loadAllData = async () => {
        setLoading(true);
        try {
            const [reqsData, convsData, friendsData] = await Promise.all([
                getFriendRequests(),
                getConversations(),
                getFriends()
            ]);
            
            setRequests(Array.isArray(reqsData) ? reqsData : []);
            setConversations(Array.isArray(convsData) ? convsData : []);
            setFriends(Array.isArray(friendsData) ? friendsData : []);

            // Set active conversation if none selected and conversations exist
            if (Array.isArray(convsData) && convsData.length > 0 && !activeConvId) {
                setActiveConvId(convsData[0].id);
            }
        } catch (error) {
            console.error("Failed to load data", error);
        } finally {
            setLoading(false);
        }
    };

    const loadMessages = async (id) => {
        try {
            const data = await getMessages(id);
            setMessages(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Failed to load messages", error);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !activeConvId) return;

        try {
            await sendMessage(activeConvId, newMessage);
            setNewMessage('');
            loadMessages(activeConvId); // Refresh messages
            // Also refresh conversations to update last message preview if we had one
            const convs = await getConversations();
            setConversations(convs);
        } catch (error) {
            console.error("Failed to send message", error);
        }
    };

    const handleAcceptRequest = async (id) => {
        try {
            await acceptFriendRequest(id);
            // Reload all data to update requests, friends list, and conversations (if chat created)
            loadAllData();
        } catch (err) {
            alert(err.message);
        }
    };

    const handleRejectRequest = async (id) => {
        try {
            await rejectFriendRequest(id);
            setRequests(prev => prev.filter(r => r.id !== id));
        } catch (err) {
            alert(err.message);
        }
    };

    const handleStartChat = async (friendId) => {
        try {
            const result = await createConversation(friendId);
            // result should be the conversation object (or contains id)
            // If backend returns { conversation_id: ... } or full object.
            // Let's assume full object or we fetch conversations again.
            
            // Reload conversations to ensure it's in the list
            const convs = await getConversations();
            setConversations(convs);
            
            // Find the conversation with this friend
            // If result has id, use it.
            const convId = result.id || result.conversation_id;
            if (convId) {
                setActiveConvId(convId);
            } else {
                // Fallback: look for conversation with this friend
                const target = convs.find(c => c.participants && c.participants.includes(friendId)); // Logic depends on data structure
                // Simplified: The backend `createConversation` likely returns the ID.
                // If not, we might need to rely on the reload.
            }
            
            if (convId) setActiveConvId(convId);
            
        } catch (err) {
            console.error("Failed to start chat", err);
            alert("Could not start chat");
        }
    };

    // Helper to get conversation name
    const getConvName = (conv) => {
        return conv.name || conv.other_user_name || "Chat";
    };

    return (
        <div className={styles.container}>
            <Card className={styles.sidebar} contentClassName={styles.cardContent} title="消息中心">
                <div className={styles.conversationList}>
                    
                    {/* Friend Requests Section - Conditional */}
                    {requests.length > 0 && (
                        <div className={styles.section}>
                            <h4 style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.9em', color: '#888', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                好友请求
                            </h4>
                            <div style={{ padding: '10px' }}>
                                {requests.map(req => (
                                    <div key={req.id} style={{
                                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                        padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', marginBottom: '5px'
                                    }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                                            {req.other_user?.avatar ? (
                                                <img src={req.other_user.avatar} alt="" style={{ width: 24, height: 24, borderRadius: '50%' }} />
                                            ) : (
                                                <User size={24} />
                                            )}
                                            <span style={{ fontSize: '0.9em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {req.other_user?.name || "Unknown"}
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', gap: '5px' }}>
                                            <button onClick={() => handleAcceptRequest(req.id)} style={{ border: 'none', background: 'green', color: '#fff', borderRadius: '4px', cursor: 'pointer', padding: '4px' }}>
                                                <Check size={14} />
                                            </button>
                                            <button onClick={() => handleRejectRequest(req.id)} style={{ border: 'none', background: 'red', color: '#fff', borderRadius: '4px', cursor: 'pointer', padding: '4px' }}>
                                                <X size={14} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Friends List Section */}
                    <div className={styles.section}>
                        <h4 style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.9em', color: '#888', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            所有好友
                        </h4>
                        <div style={{ padding: '5px' }}>
                            {friends.length === 0 && <div style={{textAlign:'center', fontSize: '0.8em', color: '#666', padding: '10px'}}>暂无好友</div>}
                            {friends.map(friend => (
                                <div key={friend.id} 
                                    onClick={() => handleStartChat(friend.id)}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: '10px',
                                        padding: '8px', cursor: 'pointer', borderRadius: '8px',
                                        transition: 'background 0.2s'
                                    }}
                                    className={styles.friendItem}
                                >
                                    {friend.avatar ? (
                                        <img src={friend.avatar} alt="" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }} />
                                    ) : (
                                        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <User size={16} />
                                        </div>
                                    )}
                                    <span style={{ fontSize: '0.9em', flex: 1 }}>{friend.name}</span>
                                    <MessageSquare size={14} color="#888" />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Conversations Section */}
                    <div className={styles.section}>
                        <h4 style={{ textAlign: 'center', padding: '10px 0', fontSize: '0.9em', color: '#888', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            会话
                        </h4>
                        {loading && <div className={styles.loading}>加载中...</div>}
                        {!loading && conversations.length === 0 && (
                            <div className={styles.emptyState}>暂无会话</div>
                        )}
                        {conversations.map(conv => (
                            <div
                                key={conv.id}
                                className={`${styles.convItem} ${activeConvId === conv.id ? styles.activeConv : ''}`}
                                onClick={() => setActiveConvId(conv.id)}
                            >
                                <div className={styles.avatar}>
                                    {getConvName(conv).charAt(0).toUpperCase()}
                                </div>
                                <div className={styles.convInfo}>
                                    <span className={styles.convName}>{getConvName(conv)}</span>
                                    {conv.last_message && (
                                        <span className={styles.lastMsg}>
                                            {conv.last_message.content?.substring(0, 20)}
                                            {conv.last_message.content?.length > 20 ? '...' : ''}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </Card>

            <div className={styles.chatArea}>
                {activeConvId ? (
                    <>
                        <div className={styles.chatHeader}>
                            {conversations.find(c => c.id === activeConvId) ? getConvName(conversations.find(c => c.id === activeConvId)) : 'Chat'}
                        </div>
                        <div className={styles.messages}>
                            {messages.map((msg, index) => {
                                const isMe = msg.sender_id === user?.id;
                                return (
                                    <div key={msg.id || index} className={`${styles.messageRow} ${isMe ? styles.myMessageRow : ''}`}>
                                        <div className={`${styles.messageBubble} ${isMe ? styles.myMessage : styles.otherMessage}`}>
                                            {msg.content}
                                        </div>
                                        <span className={styles.time}>
                                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>
                        <form onSubmit={handleSend} className={styles.inputArea}>
                            <Input
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                placeholder="Type a message..."
                                className={styles.messageInput}
                            />
                            <Button type="submit" disabled={!newMessage.trim()}>
                                <Send size={18} />
                            </Button>
                        </form>
                    </>
                ) : (
                    <div className={styles.noChatSelected}>
                        <MessageSquare size={48} color="#444" />
                        <p>Select a friend or conversation to start chatting</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatPage;
