import React from "react";
import ReactMarkdown from "react-markdown";

export default function Message({ message }) {
  const isUser = message.sender === "user";

  return (
    <div className={`message-wrapper ${isUser ? "user" : "ai"}`}>
      <div className="message-bubble">
        {isUser ? (
          message.text
        ) : (
          <ReactMarkdown>{message.text}</ReactMarkdown>
        )}
      </div>

      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="sources-container">
          <strong>Sources:</strong>
          <div className="source-badges-flex">
            {message.sources.map((src, i) => (
              <span key={i} className="source-badge">
                {src.filename} (p. {src.page})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}