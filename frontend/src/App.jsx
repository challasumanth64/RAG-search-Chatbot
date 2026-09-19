import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import "./App.css";

const API_BASE_URL = "http://localhost:8000";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleFileUpload = async (file) => {
    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "File upload failed.");
      }

      const data = await res.json();
      setDocuments((prev) => [...prev, data.filename]);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async (question) => {
    setError("");
    const userMsg = { sender: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Chat request failed.");
      }

      const data = await res.json();
      const answer = typeof data.answer === "string"
        ? data.answer
        : Array.isArray(data.answer)
          ? data.answer.map((part) => typeof part === "string" ? part : part?.text || part?.content || "").join("")
          : String(data.answer ?? "No answer was returned.");
      const aiMsg = {
        sender: "ai",
        text: answer,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        documents={documents}
        onFileUpload={handleFileUpload}
        uploading={uploading}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {error && <div className="error-banner">{error}</div>}
        <Chat
          messages={messages}
          onSendMessage={handleSendMessage}
          loading={loading}
        />
      </div>
    </div>
  );
}