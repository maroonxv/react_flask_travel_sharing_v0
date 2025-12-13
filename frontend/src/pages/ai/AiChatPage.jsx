import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import styles from './AiChatPage.module.css';
import ReactMarkdown from 'react-markdown';

const AiChatPage = () => {
  const { user } = useAuth();
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
          user_id: user?.id || 'temp_user', // Fallback for dev
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
        
        // Process complete events separated by double newline
        const events = buffer.split('\n\n');
        // Keep the last incomplete chunk in buffer
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
                  // Avoid duplicates
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
      <div className={styles.header}>
        <h2>TraeTravel AI Assistant</h2>
      </div>
      
      <div className={styles.chatWindow}>
        {messages.map((msg, index) => (
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
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask me anything about your trip..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>
          {isLoading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default AiChatPage;
