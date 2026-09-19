import React, { useState, useEffect, useRef } from "react";
import Message from "./Message";

export default function Chat({ messages, onSendMessage, loading }) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input);
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="chat-header">RAG Research Chat</div>

      <div className="messages-list">
        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {loading && <div className="loading-indicator">Thinking & retrieving context...</div>}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask a question about your documents..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
          Send ➤
        </button>
      </form>
    </div>
  );
}