import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { io } from 'socket.io-client';
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
import { Send, User, Check, X, MessageSquare, ArrowLeft, Paperclip, Smile, Plus, Users, UserPlus } from 'lucide-react';
import AddFriendModal from './AddFriendModal';
import CreateGroupModal from './CreateGroupModal';
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
    const [showAddFriend, setShowAddFriend] = useState(false);
    const [showCreateGroup, setShowCreateGroup] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const messagesEndRef = useRef(null);
    const dropdownRef = useRef(null);
    const socketRef = useRef(null);
    const activeConvIdRef = useRef(activeConvId);

    useEffect(() => {
        activeConvIdRef.current = activeConvId;
    }, [activeConvId]);

    // Socket initialization
    useEffect(() => {
        const socket = io('http://localhost:5001', {
            withCredentials: true,
            transports: ['websocket']
        });
        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('Socket connected');
        });

        socket.on('new_message', (msg) => {
            console.log('New message:', msg);
            
            // 1. Update messages if looking at this conversation
            if (activeConvIdRef.current === msg.conversation_id) {
                setMessages(prev => {
                    if (prev.find(m => m.id === msg.id)) return prev;
                    return [...prev, msg];
                });
            }

            // 2. Update conversation list preview
            setConversations(prev => prev.map(c => {
                if (c.id === msg.conversation_id) {
                    return {
                        ...c,
                        last_message: {
                            content: msg.content,
                            created_at: msg.created_at
                        }
                    };
                }
                return c;
            }));
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    // Join/Leave conversation room
    useEffect(() => {
        if (activeConvId && socketRef.current) {
            socketRef.current.emit('join', { room: activeConvId });
            return () => {
                socketRef.current.emit('leave', { room: activeConvId });
            };
        }
    }, [activeConvId]);

    useEffect(() => {
        loadAllData();
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        if (activeConvId) {
            loadMessages(activeConvId);
        }
    }, [activeConvId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setShowDropdown(false);
        }
    };

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

            if (window.innerWidth > 900 && Array.isArray(convsData) && convsData.length > 0 && !activeConvId) {
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
            loadMessages(activeConvId); 
            const convs = await getConversations();
            setConversations(convs);
        } catch (error) {
            console.error("Failed to send message", error);
        }
    };
    
    const handleInput = (e) => {
        setNewMessage(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = e.target.scrollHeight + 'px';
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(e);
            e.target.style.height = 'auto';
        }
    };

    const handleAcceptRequest = async (id) => {
        try {
            await acceptFriendRequest(id);
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
            const convs = await getConversations();
            setConversations(convs);
            
            const convId = result.id || result.conversation_id;
            if (convId) {
                setActiveConvId(convId);
            } else {
                const target = convs.find(c => c.participants && c.participants.includes(friendId)); 
                if (target) setActiveConvId(target.id);
            }
        } catch (err) {
            console.error("Failed to start chat", err);
            alert("Could not start chat");
        }
    };

    const getConvName = (conv) => {
        return conv.name || conv.other_user_name || "Chat";
    };

    const getConvAvatar = (conv) => {
        // Fallback logic if 'other_user_avatar' is not directly available, 
        // assumes backend might provide it or we use placeholder
        return conv.other_user_avatar || null;
    };
    
    const getOtherUserId = (conv) => {
        // Try to find the other user ID. 
        // If 'participants' is array of IDs and 'user.id' is known.
        if (conv.other_user_id) return conv.other_user_id;
        
        if (conv.participants && user) {
             const other = conv.participants.find(p => p !== user.id);
             return other;
        }
        return null;
    };

    const formatTime = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return '';
        
        const now = new Date();
        const diff = now - date;
        const oneDay = 24 * 60 * 60 * 1000;
        
        if (diff < oneDay && now.getDate() === date.getDate()) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        } else if (diff < 7 * oneDay) {
            return date.toLocaleDateString([], { weekday: 'short' });
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    };

    const activeConv = conversations.find(c => c.id === activeConvId);
    const otherUserId = activeConv ? getOtherUserId(activeConv) : null;

    return (
        <div className={`${styles.container} ${activeConvId ? styles.viewChat : ''}`}>
            {/* Left Sidebar */}
            <div className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <span className={styles.sidebarTitle}>Messages</span>
                    <div className={styles.headerActions} ref={dropdownRef}>
                        <button className={styles.iconBtn} onClick={() => setShowDropdown(!showDropdown)}>
                            <Plus size={20} />
                        </button>
                        {showDropdown && (
                            <div className={styles.dropdownMenu}>
                                <button className={styles.dropdownItem} onClick={() => { setShowAddFriend(true); setShowDropdown(false); }}>
                                    <UserPlus size={16} />
                                    <span>Add Friend</span>
                                </button>
                                <button className={styles.dropdownItem} onClick={() => { setShowCreateGroup(true); setShowDropdown(false); }}>
                                    <Users size={16} />
                                    <span>Create Group</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
                
                <div className={styles.conversationList}>
                    {/* Friend Requests */}
                    {requests.length > 0 && (
                        <>
                            <div className={styles.sectionTitle}>Requests</div>
                            {requests.map(req => (
                                <div key={req.id} className={styles.listItem}>
                                    <div className={styles.avatar}>
                                        {req.other_user?.avatar ? (
                                            <img src={req.other_user.avatar} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
                                        ) : <User size={20} />}
                                    </div>
                                    <span className={styles.itemName}>{req.other_user?.name || "Unknown"}</span>
                                    <div className={styles.itemMeta} style={{display: 'flex', gap: 8}}>
                                        <button onClick={(e) => { e.stopPropagation(); handleAcceptRequest(req.id); }} style={{color: '#4ade80'}}><Check size={18}/></button>
                                        <button onClick={(e) => { e.stopPropagation(); handleRejectRequest(req.id); }} style={{color: '#f87171'}}><X size={18}/></button>
                                    </div>
                                    <span className={styles.itemPreview}>Friend Request</span>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Friends List */}
                    {friends.length > 0 && (
                        <>
                            <div className={styles.sectionTitle}>Friends</div>
                            {friends.map(friend => (
                                <div key={friend.id} className={styles.listItem} onClick={() => handleStartChat(friend.id)}>
                                    <div className={styles.avatar}>
                                        {friend.avatar ? (
                                            <img src={friend.avatar} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
                                        ) : <User size={20} />}
                                    </div>
                                    <span className={styles.itemName}>{friend.name}</span>
                                    <span className={styles.itemPreview}>Click to chat</span>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Conversations */}
                    <div className={styles.sectionTitle}>Chats</div>
                    {loading && <div style={{padding: 20, textAlign: 'center', color: '#666'}}>Loading...</div>}
                    {!loading && conversations.length === 0 && (
                        <div style={{padding: 20, textAlign: 'center', color: '#666'}}>No active chats</div>
                    )}
                    {conversations.map(conv => (
                        <div
                            key={conv.id}
                            className={`${styles.listItem} ${activeConvId === conv.id ? styles.active : ''}`}
                            onClick={() => setActiveConvId(conv.id)}
                        >
                            <div className={styles.avatar}>
                                {getConvAvatar(conv) ? (
                                    <img src={getConvAvatar(conv)} alt="" style={{ width: '100%', height: '100%' }} />
                                ) : (
                                    getConvName(conv).charAt(0).toUpperCase()
                                )}
                            </div>
                            <span className={styles.itemName}>{getConvName(conv)}</span>
                            <span className={styles.itemMeta}>
                                {conv.last_message ? formatTime(conv.last_message.created_at) : ''}
                            </span>
                            <span className={styles.itemPreview}>
                                {conv.last_message?.content || 'No messages yet'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right Chat Area */}
            <div className={styles.chatArea}>
                {activeConvId ? (
                    <>
                        <div className={styles.chatHeader}>
                            <button className={styles.backButton} onClick={() => setActiveConvId(null)}>
                                <ArrowLeft size={24} />
                            </button>
                            <Link to={otherUserId ? `/users/${otherUserId}` : '#'} className={styles.avatar} style={{width: 40, height: 40, fontSize: '1rem', textDecoration: 'none'}}>
                                {activeConv && getConvAvatar(activeConv) ? (
                                    <img src={getConvAvatar(activeConv)} alt="" style={{ width: '100%', height: '100%' }} />
                                ) : (
                                    getConvName(activeConv || {}).charAt(0).toUpperCase()
                                )}
                            </Link>
                            <Link to={otherUserId ? `/users/${otherUserId}` : '#'} className={styles.headerInfo} style={{textDecoration: 'none'}}>
                                <span className={styles.headerName}>
                                    {activeConv ? getConvName(activeConv) : 'Chat'}
                                </span>
                                <span className={styles.headerStatus}>online</span>
                            </Link>
                        </div>

                        <div className={styles.messages}>
                            {messages.map((msg, index) => {
                                const isMe = msg.sender_id === user?.id;
                                const prevMsg = messages[index - 1];
                                const isChain = prevMsg && prevMsg.sender_id === msg.sender_id;
                                
                                return (
                                    <div 
                                        key={msg.id || index} 
                                        className={`${styles.messageRow} ${isMe ? styles.me : ''}`}
                                        data-chain={!isChain ? "first" : ""}
                                    >
                                        <div className={styles.messageBubble}>
                                            {msg.content}
                                        </div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className={styles.inputContainer}>
                            <form onSubmit={handleSend} className={styles.inputWrapper}>
                                <button type="button" className={styles.attachBtn}>
                                    <Paperclip size={20} />
                                </button>
                                <textarea
                                    value={newMessage}
                                    onChange={handleInput}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Message..."
                                    className={styles.inputField}
                                    rows={1}
                                />
                                <button type="button" className={styles.attachBtn}>
                                    <Smile size={20} />
                                </button>
                                <button type="submit" className={styles.sendBtn} disabled={!newMessage.trim()}>
                                    <Send size={20} />
                                </button>
                            </form>
                        </div>
                    </>
                ) : (
                    <div className={styles.noChat}>
                        <div className={styles.noChatIcon}>
                            <MessageSquare size={32} />
                        </div>
                        <p>Select a chat to start messaging</p>
                    </div>
                )}
            </div>

            {showAddFriend && <AddFriendModal onClose={() => setShowAddFriend(false)} />}
            {showCreateGroup && (
                <CreateGroupModal 
                    onClose={() => setShowCreateGroup(false)} 
                    onSuccess={loadAllData} 
                />
            )}
        </div>
    );
};

export default ChatPage;
