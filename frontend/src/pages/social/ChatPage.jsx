import { useState, useEffect, useRef } from 'react';
import { getConversations, getMessages, sendMessage } from '../../api/social';
import { useAuth } from '../../context/AuthContext';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Card from '../../components/Card';
import { Send, User } from 'lucide-react';
import styles from './ChatPage.module.css';

const ChatPage = () => {
    const { user } = useAuth();
    const [conversations, setConversations] = useState([]);
    const [activeConvId, setActiveConvId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadConversations();
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

    const loadConversations = async () => {
        try {
            const data = await getConversations();
            setConversations(Array.isArray(data) ? data : []);
            if (data.length > 0 && !activeConvId) {
                setActiveConvId(data[0].id);
            }
        } catch (error) {
            console.error("Failed to load conversations", error);
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
        } catch (error) {
            console.error("Failed to send message", error);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.sidebar} contentClassName={styles.cardContent} title="消息列表">
                <div className={styles.conversationList}>
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
                                {conv.other_user_name?.charAt(0).toUpperCase()}
                            </div>
                            <div className={styles.convInfo}>
                                <span className={styles.convName}>{conv.name || conv.other_user_name}</span>
                                <span className={styles.convLastMsg}>{conv.last_message_content}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </Card>

            <Card className={styles.chatArea} contentClassName={styles.cardContent}>
                {activeConvId ? (
                    <>
                        <div className={styles.chatHeader}>
                            <h3>{conversations.find(c => c.id === activeConvId)?.name || '聊天'}</h3>
                        </div>

                        <div className={styles.messageList}>
                            {messages.map((msg, idx) => {
                                const isMe = msg.sender_id === user?.id;
                                return (
                                    <div key={idx} className={`${styles.message} ${isMe ? styles.sent : styles.received}`}>
                                        <div className={styles.bubble}>
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
                                placeholder="输入消息..."
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                className={styles.chatInput}
                                style={{ marginBottom: 0 }}
                            />
                            <Button type="submit" variant="social" className={styles.sendBtn} disabled={!newMessage.trim()}>
                                <Send size={18} />
                            </Button>
                        </form>
                    </>
                ) : (
                    <div className={styles.noChatSelected}>
                        <User size={48} />
                        <p>选择一个会话开始聊天</p>
                    </div>
                )}
            </Card>
        </div>
    );
};

export default ChatPage;
