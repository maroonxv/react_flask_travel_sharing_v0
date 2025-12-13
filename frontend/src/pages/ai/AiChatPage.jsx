import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import styles from './AiChatPage.module.css';
import ReactMarkdown from 'react-markdown';
import { MessageSquare, Plus, Clock, Bot, Send } from 'lucide-react';
import { toast } from 'react-hot-toast';

const AiChatPage = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (user) {
        fetchConversations();
    }
  }, [user]);

  useEffect(() => {
      if (conversationId) {
          fetchMessages(conversationId);
      } else {
          setMessages([]);
      }
  }, [conversationId]);

  const fetchConversations = async () => {
      try {
          const response = await fetch(`http://localhost:5001/api/ai/conversations?user_id=${user?.id || 'temp_user'}`);
          if (response.ok) {
              const data = await response.json();
              setConversations(data);
          }
      } catch (error) {
          console.error("Failed to load conversations", error);
      }
  };

  const fetchMessages = async (id) => {
      setIsLoading(true);
      try {
          const response = await fetch(`http://localhost:5001/api/ai/conversations/${id}?user_id=${user?.id || 'temp_user'}`);
          if (response.ok) {
              const data = await response.json();
              setMessages(data.messages || []);
          }
      } catch (error) {
          console.error("Failed to load messages", error);
          toast.error("加载消息失败");
      } finally {
          setIsLoading(false);
      }
  };

  const handleNewChat = () => {
      setConversationId(null);
      setMessages([]);
      setInput('');
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5001/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user?.id || 'temp_user',
          message: userMessage.content,
          conversation_id: conversationId
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      // Initialize AI message placeholder
      setMessages(prev => [...prev, { role: 'assistant', content: '', attachments: [] }]);
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        const events = buffer.split('\n\n');
        buffer = events.pop();

        for (const eventStr of events) {
            if (!eventStr.trim()) continue;
            
            const lines = eventStr.split('\n');
            let eventType = null;
            let eventData = null;

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.substring(7).trim();
                } else if (line.startsWith('data: ')) {
                    try {
                        eventData = JSON.parse(line.substring(6));
                    } catch (e) {
                        console.error('JSON Parse Error', e);
                    }
                }
            }

            if (eventType && eventData) {
                handleSseEvent(eventType, eventData);
            }
        }
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { role: 'system', content: 'Error: Could not connect to AI service.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSseEvent = (type, data) => {
      if (type === 'init') {
          setConversationId(data.conversation_id);
          // Refresh conversation list to show the new one
          fetchConversations();
      } else if (type === 'text_chunk') {
          setMessages(prev => {
              const newMessages = [...prev];
              const lastMsg = newMessages[newMessages.length - 1];
              if (lastMsg.role === 'assistant') {
                  lastMsg.content += data.delta;
              }
              return newMessages;
          });
      } else if (type === 'attachment') {
          setMessages(prev => {
              const newMessages = [...prev];
              const lastMsg = newMessages[newMessages.length - 1];
              if (lastMsg.role === 'assistant') {
                  if (!lastMsg.attachments) lastMsg.attachments = [];
                  if (!lastMsg.attachments.some(a => a.reference_id === data.reference_id)) {
                      lastMsg.attachments.push(data);
                  }
              }
              return newMessages;
          });
      }
  };

  return (
    <div className={styles.container}>
      {/* Sidebar - History */}
      <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>
              <span className={styles.linkText}>TripMate</span>
              <button className={styles.newChatBtn} onClick={handleNewChat} title="新建对话">
                  <Plus size={20} />
              </button>
          </div>
          <div className={styles.conversationList}>
              {conversations.length === 0 && (
                  <div style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem' }}>
                      暂无历史对话
                  </div>
              )}
              {conversations.map(conv => (
                  <div 
                      key={conv.id} 
                      className={`${styles.historyItem} ${conversationId === conv.id ? styles.active : ''}`}
                      onClick={() => setConversationId(conv.id)}
                  >
                      <div className={styles.historyTitle}>{conv.title || '新对话'}</div>
                      <div className={styles.historyDate}>
                          <Clock size={12} style={{ marginRight: 4, display: 'inline-block', verticalAlign: 'middle' }} />
                          {new Date(conv.updated_at).toLocaleDateString()}
                      </div>
                  </div>
              ))}
          </div>
      </div>

      {/* Main Chat Area */}
      <div className={styles.mainArea}>
          <div className={styles.chatHeader}>
              <span className={styles.chatTitle}>
                  {conversationId ? (conversations.find(c => c.id === conversationId)?.title || '对话') : '新对话'}
              </span>
          </div>

          <div className={styles.chatWindow}>
            {messages.length === 0 ? (
                <div className={styles.emptyState}>
                    <Bot size={64} className={styles.emptyIcon} />
                    <p>你好！我是你的旅行 AI 助手。</p>
                    <p>我可以帮你规划行程、推荐景点，或者回答关于旅行的问题。</p>
                </div>
            ) : (
                messages.map((msg, index) => (
                <div key={index} className={`${styles.message} ${styles[msg.role]}`}>
                    <div className={styles.bubble}>
                        {msg.role === 'assistant' ? (
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        ) : (
                            msg.content
                        )}
                    </div>
                    
                    {msg.attachments && msg.attachments.length > 0 && (
                        <div className={styles.attachments}>
                            {msg.attachments.map((att, i) => (
                                <div key={i} className={styles.card}>
                                    <div className={styles.cardType}>{att.type.toUpperCase()}</div>
                                    <div className={styles.cardTitle}>{att.title}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className={styles.inputArea}>
            <div className={styles.inputWrapper}>
                <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="问我任何关于旅行的问题..."
                disabled={isLoading}
                />
                <button className={styles.sendBtn} onClick={handleSend} disabled={isLoading || !input.trim()}>
                    {isLoading ? '...' : <Send size={20} />}
                </button>
            </div>
          </div>
      </div>
    </div>
  );
};

export default AiChatPage;
