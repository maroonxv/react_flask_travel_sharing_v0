import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { io } from 'socket.io-client';
import EmojiPicker from 'emoji-picker-react';
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
import { Send, User, Check, X, MessageSquare, ArrowLeft, Smile, Plus, Users, UserPlus, Image as ImageIcon } from 'lucide-react';
import AddFriendModal from './AddFriendModal';
import CreateGroupModal from './CreateGroupModal';
import LoadingSpinner from '../../components/LoadingSpinner';
import toast from 'react-hot-toast';
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
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    
    const messagesEndRef = useRef(null);
    const dropdownRef = useRef(null);
    const socketRef = useRef(null);
    const activeConvIdRef = useRef(activeConvId);
    const fileInputRef = useRef(null);
    const emojiPickerRef = useRef(null);

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

    const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
            setShowDropdown(false);
        }
        if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target) && !event.target.closest(`.${styles.attachBtn}`)) {
            setShowEmojiPicker(false);
        }
    };

    useEffect(() => {
        if (activeConvId) {
            loadMessages(activeConvId);
            setNewMessage('');
            setSelectedFile(null);
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

            if (window.innerWidth > 900 && Array.isArray(convsData) && convsData.length > 0 && !activeConvId) {
                setActiveConvId(convsData[0].id);
            }
        } catch (error) {
            console.error("Failed to load data", error);
            toast.error("加载数据失败");
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
            toast.error("加载消息失败");
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            toast.error('不支持的文件类型，请选择图片');
            return;
        }

        setSelectedFile(file);
        // Reset value so same file can be selected again if cleared
        e.target.value = '';
    };

    const removeFile = () => {
        setSelectedFile(null);
    };

    const handleEmojiClick = (emojiObject) => {
        setNewMessage(prev => prev + emojiObject.emoji);
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if ((!newMessage.trim() && !selectedFile) || !activeConvId) return;

        try {
            let payload;
            if (selectedFile) {
                const formData = new FormData();
                formData.append('content', newMessage); // Caption
                formData.append('type', 'image');
                formData.append('media_file', selectedFile);
                payload = formData;
            } else {
                payload = newMessage; // Simple text
            }

            await sendMessage(activeConvId, payload);
            setNewMessage('');
            setSelectedFile(null);
            setShowEmojiPicker(false);
            
            // Optimistic update or wait for socket? 
            // Socket usually handles it, but let's reload to be safe or rely on socket.
            // Socket update is already handled in useEffect.
            
            // loadMessages(activeConvId); 
            // const convs = await getConversations();
            // setConversations(convs);
        } catch (error) {
            console.error("Failed to send message", error);
            toast.error("发送失败");
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
            toast.success("已接受好友请求");
            loadAllData();
        } catch (err) {
            toast.error(err.message);
        }
    };

    const handleRejectRequest = async (id) => {
        try {
            await rejectFriendRequest(id);
            setRequests(prev => prev.filter(r => r.id !== id));
            toast.success("已拒绝好友请求");
        } catch (err) {
            toast.error(err.message);
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
            toast.error("无法开始聊天");
        }
    };

    const getConvName = (conv) => {
        return conv.name || conv.other_user_name || "聊天";
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
                    <span className={styles.sidebarTitle}>消息</span>
                    <div className={styles.headerActions} ref={dropdownRef}>
                        <button className={styles.iconBtn} onClick={() => setShowDropdown(!showDropdown)}>
                            <Plus size={20} />
                        </button>
                        {showDropdown && (
                            <div className={styles.dropdownMenu}>
                                <button className={styles.dropdownItem} onClick={() => { setShowAddFriend(true); setShowDropdown(false); }}>
                                    <UserPlus size={16} />
                                    <span>添加好友</span>
                                </button>
                                <button className={styles.dropdownItem} onClick={() => { setShowCreateGroup(true); setShowDropdown(false); }}>
                                    <Users size={16} />
                                    <span>发起群聊</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
                
                <div className={styles.conversationList}>
                    {/* Friend Requests */}
                    {requests.length > 0 && (
                        <>
                            <div className={styles.sectionTitle}>好友请求</div>
                            {requests.map(req => (
                                <div key={req.id} className={styles.listItem}>
                                    <div className={styles.avatar}>
                                        {req.other_user?.avatar ? (
                                            <img src={req.other_user.avatar} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
                                        ) : <User size={20} />}
                                    </div>
                                    <span className={styles.itemName}>{req.other_user?.name || "未知用户"}</span>
                                    <div className={styles.itemMeta} style={{display: 'flex', gap: 8}}>
                                        <button onClick={(e) => { e.stopPropagation(); handleAcceptRequest(req.id); }} style={{color: '#4ade80', background: 'none', border: 'none', cursor: 'pointer'}}><Check size={18}/></button>
                                        <button onClick={(e) => { e.stopPropagation(); handleRejectRequest(req.id); }} style={{color: '#f87171', background: 'none', border: 'none', cursor: 'pointer'}}><X size={18}/></button>
                                    </div>
                                    <span className={styles.itemPreview}>好友请求</span>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Friends List */}
                    {friends.length > 0 && (
                        <>
                            <div className={styles.sectionTitle}>好友</div>
                            {friends.map(friend => (
                                <div key={friend.id} className={styles.listItem} onClick={() => handleStartChat(friend.id)}>
                                    <div className={styles.avatar}>
                                        {friend.avatar ? (
                                            <img src={friend.avatar} alt="" style={{ width: '100%', height: '100%', borderRadius: '50%' }} />
                                        ) : <User size={20} />}
                                    </div>
                                    <span className={styles.itemName}>{friend.name}</span>
                                    <span className={styles.itemPreview}>点击发起聊天</span>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Conversations */}
                    <div className={styles.sectionTitle}>聊天</div>
                    {loading && <div className={styles.loadingContainer}><LoadingSpinner size="medium" /></div>}
                    {!loading && conversations.length === 0 && (
                        <div className={styles.emptyState}>暂无聊天</div>
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
                                {conv.last_message?.content || '暂无消息'}
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
                            <Link to={otherUserId ? `/profile/${otherUserId}` : '#'} className={styles.avatar} style={{width: 40, height: 40, fontSize: '1rem', textDecoration: 'none'}}>
                                {activeConv && getConvAvatar(activeConv) ? (
                                    <img src={getConvAvatar(activeConv)} alt="" style={{ width: '100%', height: '100%' }} />
                                ) : (
                                    getConvName(activeConv || {}).charAt(0).toUpperCase()
                                )}
                            </Link>
                            <Link to={otherUserId ? `/profile/${otherUserId}` : '#'} className={styles.headerInfo} style={{textDecoration: 'none'}}>
                                <span className={styles.headerName}>
                                    {activeConv ? getConvName(activeConv) : '聊天'}
                                </span>
                                <span className={styles.headerStatus}>在线</span>
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
                                            {msg.type === 'image' ? (
                                                <div className={styles.imageMessage}>
                                                    <img src={msg.media_url} alt="Shared" className={styles.msgImage} />
                                                    {msg.content && <p className={styles.imageCaption}>{msg.content}</p>}
                                                </div>
                                            ) : msg.type === 'share_post' ? (
                                                <div className={styles.shareMessage}>
                                                    <p className={styles.shareText}>{msg.content}</p>
                                                    <Link to={`/social/post/${msg.reference_id}`} className={styles.shareLink}>
                                                        <div className={styles.shareCard}>
                                                            <span>查看分享的帖子</span>
                                                            <ArrowLeft size={16} style={{transform: 'rotate(180deg)'}} />
                                                        </div>
                                                    </Link>
                                                </div>
                                            ) : (
                                                msg.content
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>

                        <div className={styles.inputContainer}>
                            {selectedFile && (
                                <div className={styles.filePreview}>
                                    <div className={styles.previewItem}>
                                        <ImageIcon size={16} />
                                        <span className={styles.fileName}>{selectedFile.name}</span>
                                        <button type="button" onClick={removeFile} className={styles.removeFileBtn}>
                                            <X size={14} />
                                        </button>
                                    </div>
                                </div>
                            )}
                            
                            <form onSubmit={handleSend} className={styles.inputWrapper}>
                                <input 
                                    type="file" 
                                    ref={fileInputRef}
                                    style={{display: 'none'}} 
                                    accept="image/*"
                                    onChange={handleFileSelect}
                                />
                                <button type="button" className={styles.attachBtn} onClick={() => fileInputRef.current?.click()}>
                                    <ImageIcon size={20} />
                                </button>
                                <textarea
                                    value={newMessage}
                                    onChange={handleInput}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Message..."
                                    className={styles.inputField}
                                    rows={1}
                                />
                                <div className={styles.emojiWrapper} ref={emojiPickerRef}>
                                    <button 
                                        type="button" 
                                        className={styles.attachBtn} 
                                        onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                                    >
                                        <Smile size={20} />
                                    </button>
                                    {showEmojiPicker && (
                                        <div className={styles.emojiPickerContainer}>
                                            <EmojiPicker onEmojiClick={handleEmojiClick} width={300} height={400} />
                                        </div>
                                    )}
                                </div>
                                <button type="submit" className={styles.sendBtn} disabled={!newMessage.trim() && !selectedFile}>
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
                        <p>选择一个聊天开始发送消息</p>
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
